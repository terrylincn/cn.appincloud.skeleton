import omni.ext
import omni.ui as ui
from .skeletonutils import addRootToUsd, copyAnim, copyAnimToUsd, copyRotation, copySkel
import uuid 
import carb
import os
from pxr import Usd,UsdSkel,AnimationSchema
from omni.kit.window.popup_dialog import MessageDialog

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[cn.appincloud.skeleton] MyExtension startup")

        self._window = ui.Window("Avatar convert", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                ui.Label("add root joint to skeleton")

                def on_add_joint_click():
                    print("add clicked!")
                    self._on_assign_selected()

                def _copy_skel_click():
                    print("copy skel clicked!")
                    self._copy_skel()

                def _copy_anim_click():
                    print("copy anim clicked!")
                    self._copy_anim()

                def _copy_rot_click():
                    print("copy rot clicked!")
                    self._copy_rot()

                ui.Button("Add Root Joint", clicked_fn=lambda: on_add_joint_click())
                ui.Button("Copy Skeleton", clicked_fn=lambda: _copy_skel_click())
                ui.Button("Copy Animation", clicked_fn=lambda: _copy_anim_click())
                ui.Button("Copy Rotation", clicked_fn=lambda: _copy_rot_click())

    def on_shutdown(self):
        print("[cn.appincloud.skeleton] MyExtension shutdown")

    def _on_assign_selected(self):
        # find currently seleced joint
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        selection = usd_context.get_selection()
        selected_prims = selection.get_selected_prim_paths()
        skeleton = None
        if len(selected_prims) > 0:
            prim = stage.GetPrimAtPath(selected_prims[0])
            print(prim)
            if AnimationSchema.SkelJoint(prim):
                skeleton, joint_token = AnimationSchema.SkelJoint(prim).GetJoint()
            elif UsdSkel.Skeleton(prim):
                print("skeleton")
                #skeleton = UsdSkel.Skeleton(prim)
                #addJoint(skeleton)
                #print(skeleton.GetRestTransformsAttr().Get())
            elif UsdSkel.Root(prim):
                print("skeleton root", selected_prims[0])
                file_url = usd_context.get_stage_url()
                prim_url = omni.usd.get_url_from_prim(prim)
                print(file_url, prim_url)
                if prim_url is not None and file_url != prim_url:
                    usd_context.open_stage(prim_url)
                    stage = usd_context.get_stage()
                    prim_path = "/World/Hips0"
                    prim = stage.GetPrimAtPath(prim_path)
                else:
                    prim_url = file_url
                if prim_url is None or prim_url.startswith("omniverse:"):
                    tmp_dir = carb.tokens.get_tokens_interface().resolve("${shared_documents}/capture/temp")
                    tmp_fname = "stage_test_" + str(uuid.uuid4()) + ".usda"
                    tmp_fpath = os.path.normpath(os.path.abspath(os.path.join(tmp_dir, tmp_fname)))
                else:
                    tmp_fpath = prim_url.replace(".usd",".usda")
                root = UsdSkel.Root(prim)
                prims = prim.GetChildren()
                for subprim in prims:
                    if UsdSkel.Skeleton(subprim):
                        skel = UsdSkel.Skeleton(subprim)
                        addRootToUsd(skel, tmp_fpath)
                        #stage = Usd.Stage.Open(tmp_fpath)
                        print("loading...")
                        stage = usd_context.open_stage(tmp_fpath)
                        usd_context.attach_stage_with_callback(stage)
                        break
        else:
            dialog = MessageDialog(title="no prim selected", message="please select a prim", disable_okay_button=True, disable_cancel_button=False)
            dialog.show()

    def _copy_skel(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        selection = usd_context.get_selection()
        selected_prims = selection.get_selected_prim_paths()
        skeleton = None
        if len(selected_prims) > 1:
            prim1 = stage.GetPrimAtPath(selected_prims[0])
            prim2 = stage.GetPrimAtPath(selected_prims[1])
            print(prim1, prim2)
            copySkel(prim1, prim2)

    def _copy_anim(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        selection = usd_context.get_selection()
        selected_prims = selection.get_selected_prim_paths()
        if len(selected_prims) > 1:
            _source_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath(selected_prims[0]))
            _target_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath(selected_prims[1]))
            copyAnim(_source_skeleton, _target_skeleton, "/World/testanim")
        else:
            return

    def _copy_rot(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        selection = usd_context.get_selection()
        selected_prims = selection.get_selected_prim_paths()
        if len(selected_prims) > 0:
            _source_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath(selected_prims[0]))
            copyRotation(_source_skeleton, "/World/testanim")
        else:
            return