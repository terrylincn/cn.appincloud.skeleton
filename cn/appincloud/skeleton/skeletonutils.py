
import omni
from pxr import Usd, UsdSkel, Vt, Gf
import numpy as np
import copy
from omni.anim.retarget.core.scripts.utils import (
    convert_matrix_to_trans_rots,
    convert_trans_rots_to_pxr
)
import carb
import os
import uuid

root_rest_translations = ((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
def addJoint(skel):    
    def translation2transform(vec):
        t = np.eye(4)
        t[:-1, -1] = vec
        return t.T

    skel_cache = UsdSkel.Cache()
    skel_query = skel_cache.GetSkelQuery(skel)
    joint_tokens = skel.GetJointsAttr().Get()#skel_query.GetJointOrder()

    root_t = copy.deepcopy(root_rest_translations)

    rest_translations = [root_t] + np.asarray(skel.GetRestTransformsAttr().Get())
    bind_translations = [root_t] + np.asarray(skel.GetBindTransformsAttr().Get())
    
    rest_transforms = Vt.Matrix4dArray.FromNumpy(
        rest_translations
        #np.array([translation2transform(x) for x in rest_translations])
    )
    bind_transforms = Vt.Matrix4dArray.FromNumpy(
        bind_translations
        #np.array([translation2transform(x) for x in bind_translations])
    )
    
    joint_tokens = ["root"] + ["root/" + token for token in joint_tokens]

    skel_cache.Clear()
    skel.GetRestTransformsAttr().Set(rest_transforms)
    skel.GetBindTransformsAttr().Set(bind_transforms)
    skel.GetJointsAttr().Set(joint_tokens)

    """
    anim = UsdSkel.Animation.Define(stage, root_path + "/Skeleton/Anim")
    anim.GetJointsAttr().Set(joint_tokens)

    binding = UsdSkel.BindingAPI.Apply(skel.GetPrim())
    binding.CreateAnimationSourceRel().SetTargets([anim.GetPrim().GetPath()])
    binding = UsdSkel.BindingAPI.Apply(skel_root.GetPrim())
    binding.CreateSkeletonRel().SetTargets([skel.GetPrim().GetPath()])
    """

def save_as_usda(fpath):
    omni.usd.get_context().save_as_stage(fpath)

def add_root(content, skelroot="Hips0", joint="Hips"):
    content = content.replace(skelroot, "skelroot")
    content = content.replace(joint, "Root/" + joint)
    content = content.replace("uniform matrix4d[] restTransforms = [", "uniform matrix4d[] restTransforms = [((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1)),")
    content = content.replace("uniform matrix4d[] bindTransforms = [", "uniform matrix4d[] bindTransforms = [((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1)),")
    content = content.replace('uniform token[] joints = [', 'uniform token[] joints = ["Root",')
    return content

def load_usda(fpath):
    with open(fpath, 'r') as fp:
        content = fp.read()
    return content

def save_usda(fpath, content):
    with open(fpath, 'w') as fp:
        fp.write(content)

def addRootToUsd(skel, fpath):
    save_as_usda(fpath)
    content = load_usda(fpath)
    content = add_root(content)
    save_usda(fpath, content)

def copySkel(source_prim, target_prim):
    #interpolation = "vertex"
    elementSize = 4
    source_binding = UsdSkel.BindingAPI.Apply(source_prim)
    target_binding = UsdSkel.BindingAPI.Apply(target_prim)
    joints = source_binding.GetJointsAttr()
    target_binding.CreateJointsAttr().Set(joints.Get())
    jointIndices = source_binding.GetJointIndicesAttr()
    target_binding.CreateJointIndicesAttr().Set(jointIndices.Get())
    target_binding.CreateJointIndicesPrimvar(constant=False,elementSize=elementSize)
    jointWeights = source_binding.GetJointWeightsAttr()
    target_binding.CreateJointWeightsAttr().Set(jointWeights.Get())
    target_binding.CreateJointWeightsPrimvar(constant=False,elementSize=elementSize)
    geomBind = source_binding.GetGeomBindTransformAttr()
    target_binding.CreateGeomBindTransformAttr().Set(geomBind.Get())
    skelRel = source_binding.GetSkeletonRel().GetTargets()
    target_binding.CreateSkeletonRel().SetTargets(skelRel)

def convert_to_trans_rots(translations1, rotations1):
    translations: List[carb.Float3] = []
    rotations: List[carb.Float4] = []

    for trans in translations1:
        translations.append(carb.Float3(trans[0], trans[1], trans[2]))
    for quat in rotations1:
        rotations.append(carb.Float4(quat.imaginary[0], quat.imaginary[1], quat.imaginary[2], quat.real))

    return translations, rotations

def copyAnim(source_skeleton, target_skeleton, prim_path):
    
        retarget_controller = omni.anim.retarget.core.RetargetController(
            "",
            source_skeleton.GetPath().pathString,
            target_skeleton.GetPath().pathString
        )

        if (source_skeleton and target_skeleton):
            stage = omni.usd.get_context().get_stage()
            time_code = omni.timeline.get_timeline_interface().get_current_time() * stage.GetTimeCodesPerSecond()
            # copy source transform
            source_skel_cache = UsdSkel.Cache()
            source_skel_query = source_skel_cache.GetSkelQuery(source_skeleton)
            source_transforms = source_skel_query.ComputeJointLocalTransforms(time_code)
            source_translations, source_rotations = convert_matrix_to_trans_rots(source_transforms)

            joint_tokens = target_skeleton.GetJointsAttr().Get()
            #skel_cache = UsdSkel.Cache()
            #skel_query = skel_cache.GetSkelQuery(target_skeleton)
            target_translations, target_rotations = retarget_controller.retarget(source_translations, source_rotations)
            t1, t2, t3 =convert_trans_rots_to_pxr(target_translations, target_rotations)

            """ this only gets one
            source_binding = UsdSkel.BindingAPI.Apply(source_skeleton.GetPrim())
            source_prim = source_binding.GetAnimationSource()
            source_anim = UsdSkel.Animation.Get(stage, source_prim.GetPath())
            source_translations = source_anim.GetTranslationsAttr().Get()
            source_rotations = source_anim.GetRotationsAttr().Get()
            source_translations, source_rotations = convert_to_trans_rots(source_translations, source_rotations)
            """
            suurce_anim_query =  source_skel_query.GetAnimQuery()
            #source_skel_anim = UsdSkel.Animation(suurce_anim_query.GetPrim())
            jtt = suurce_anim_query.GetJointTransformTimeSamples()
            prim = suurce_anim_query.GetPrim()
            prim_path = prim.GetPath().pathString + "_target"
            carb.log_info("jtt:{}".format(jtt))

            target_anim = UsdSkel.Animation.Define(stage, prim_path)
            target_anim.CreateJointsAttr().Set(joint_tokens)
            transAttr = target_anim.CreateTranslationsAttr()
            rotAttr = target_anim.CreateRotationsAttr()
            scalAttr = target_anim.CreateScalesAttr()

            tt1 = {}
            tt2 = {}
            for jt in jtt:
                source_transforms = suurce_anim_query.ComputeJointLocalTransforms(Usd.TimeCode(jt))
                source_translations, source_rotations = convert_matrix_to_trans_rots(source_transforms)
                carb.log_info("time:{} source_translations:{} source_rotations:{}".format(jt, source_translations, source_rotations))
            
                # retarget
                target_translations: List[carb.Float3] = []
                target_rotations: List[carb.Float4] = []
                target_translations, target_rotations = retarget_controller.retarget(source_translations, source_rotations)
                tt1[jt] = target_translations
                tt2[jt] = target_rotations
                target_translations, target_rotations, target_scales = convert_trans_rots_to_pxr(target_translations, target_rotations)
                transAttr.Set(target_translations, Usd.TimeCode(jt))
                rotAttr.Set(target_rotations, Usd.TimeCode(jt))
                scalAttr.Set(target_scales, Usd.TimeCode(jt))
                
            """
            omni.usd.get_context().new_stage()
            new_stage = omni.usd.get_context().get_stage()
            target_anim = UsdSkel.Animation.Define(new_stage, "/World")
            target_anim.CreateJointsAttr().Set(joint_tokens)
            target_anim.CreateTranslationsAttr().Set(t1)
            target_anim.CreateRotationsAttr().Set(t2)
            target_anim.CreateScalesAttr().Set(t3)
            """
        return tt1, tt2

def add_timesamples(translations, rotations, content):
    content = content.replace('SkelAnimation "World"', 'SkelAnimation "World"(apiSchemas = ["AnimationSkelBindingAPI"])')
    txt1 = '\nfloat3[] translations.timeSamples = {'
    for key, translation in translations.items():
        txt1 += '{}:{},\n'.format(key, translation).replace("carb.Float3","")
    txt1 += '}\n'
    txt2 = '\nquatf[] rotations.timeSamples = {'
    for key, rotation in rotations.items():
        txt2 += '{}:{},\n'.format(key, rotation).replace("carb.Float4","")
    txt2 += '}\n'
    carb.log_info(txt1)
    carb.log_info(txt2)
    newcontent = content[:content.rfind("}")-1] + txt1 + txt2 + '}'
    return newcontent

def copyAnimToUsd(source_skeleton, target_skeleton, prim_path):
    tmp_dir = carb.tokens.get_tokens_interface().resolve("${shared_documents}/capture/temp")
    tmp_fname = "stage_test_" + str(uuid.uuid4()) + ".usda"
    fpath = os.path.normpath(os.path.abspath(os.path.join(tmp_dir, tmp_fname)))
    tt1, tt2 = copyAnim(source_skeleton, target_skeleton, prim_path)
    save_as_usda(fpath)
    content = load_usda(fpath)
    content = add_timesamples(tt1, tt2, content)
    save_usda(fpath, content)

def extract_transforms(source_transforms):
    source_translations = []
    source_rotations = []
    for source_transform in source_transforms:
        source_translations.append(source_transform.ExtractTranslation())
        source_rotations.append(source_transform.ExtractRotation())
    return source_translations, source_rotations

def copyRotation(source_skeleton, prim_path):
        if (source_skeleton):
            stage = omni.usd.get_context().get_stage()
            time_code = omni.timeline.get_timeline_interface().get_current_time() * stage.GetTimeCodesPerSecond()
            # copy source transform
            source_skel_cache = UsdSkel.Cache()
            source_skel_query = source_skel_cache.GetSkelQuery(source_skeleton)
            #source_transforms = source_skel_query.ComputeJointLocalTransforms(time_code)
            #source_translations, source_rotations = convert_matrix_to_trans_rots(source_transforms)
            source_transforms = source_skeleton.GetBindTransformsAttr().Get()
            source_transforms = source_skeleton.GetRestTransformsAttr().Get()
            source_translations, source_rotations = convert_matrix_to_trans_rots(source_transforms)
            source_translations, source_rotations, source_scales = convert_trans_rots_to_pxr(source_translations, source_rotations)

            joint_tokens = source_skeleton.GetJointsAttr().Get()

            target_anim = UsdSkel.Animation.Define(stage, prim_path)
            target_anim.CreateJointsAttr().Set(joint_tokens)
            target_anim.CreateTranslationsAttr().Set(source_translations)
            target_anim.CreateRotationsAttr().Set(source_rotations)
            target_anim.CreateScalesAttr().Set(source_scales)