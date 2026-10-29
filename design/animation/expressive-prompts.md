# 夸张跑步素材生成记录

工具：内置 `image_gen`，透明背景，无 CLI / API 回退。
参考：用户提供的第二张 Q 版侧面大步跑图。
最终素材：`assets/rig/expressive-run.png`；左侧为扬发头部，右侧为敞开衣身。程序按区域读取，原版保留原有独立头部。

## 首次提示词

Use case: identity-preserve sprite adaptation. Reference is the exact desired girlfriend chibi character, preserve her face, large brown eyes, thin round gold glasses, dark brown long wavy hair, ivory jacket and detailed painted chibi rendering. Produce a transparent 1536x1024 atlas with EXACTLY TWO separate isolated components, generous space between them, no labels. LEFT region x20..1000: her detached entire head, glasses and ALL long hair flowing far BACKWARD TO THE LEFT in a strong joyful running motion, like the reference. Head faces strictly screen RIGHT in pure side profile, same face and hair style, tiny nose and mouth. Hair sweeps backward in an airborne broad arc, NOT hanging down vertically, includes curled trailing locks. NO body, clothing, shoulders, arms or hands in this left component. RIGHT region x1080..1510 centered vertically: just the detached ivory jacket TORSO and cream sweater underneath, with hood at upper back, side-profile facing RIGHT, no head, no sleeves, no arms, no hands, no legs. This torso is a lively OPEN jacket with visible sweater front and flared loose jacket tails billowing BACKWARD left, asymmetric curved hem, dynamic folds as in the reference. Continuous ivory fabric at shoulder attachment, NO circular empty socket or visible armhole. Torso's main shoulder-to-hip axis is upright for animation, but jacket rear fabric flares to the left. Both pieces exactly match the reference illustration's colors, shading and linework. Actual transparent background, no glow or ground shadow. Keep everything within canvas and do not let two components overlap.

## 定向修正提示词

Precise localized sprite edit. Keep the entire LEFT head/hair/glasses component pixel-faithful, unchanged in scale and position. Edit only the RIGHT jacket object: it currently accidentally has an attached sleeve sticking left. REMOVE THAT ENTIRE SLEEVE AND ITS HOLLOW CUFF. Output a sleeveless torso cutout for a puppet, with the near shoulder filled with continuous cream jacket fabric, no armhole, no oval sockets, no tubular sleeve shapes anywhere. Keep the open jacket zipper, cream sweater front, ivory hood. Make the lower LEFT BACK HEM a short flared open flap of jacket fabric that tapers naturally, NOT a sleeve or cuff. Side view facing right, same placement and style. Keep head and torso separate. Preserve transparent alpha and 1536x1024 canvas. No new body parts, text, background, shadows or glow.
