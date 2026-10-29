# 原版头部尺寸校正

原始整帧1、8头部偏大，7略小。使用内置 imagegen 定向编辑完整图片，以第3帧为头部尺寸参照；保留身体姿势和固定整体缩放，更新眼睛对齐坐标。

最终图片：assets/whole-run/natural/01.png、07.png、08.png。

八帧等比例、眼睛对齐的检查图：natural-head-size-corrected.png。检查时以脸部、眼镜和下颌为准，不把飘动的发梢当作头部外框。

## 第1帧提示词

Precise localized animation consistency edit. Image1 is the TARGET whole running sprite, image2 supplies ONLY the correct HEAD SIZE. Preserve image1's entire running pose, both arms/hands, torso/jacket, hips, legs and shoes, size and position on the exact 1536x1024 transparent canvas. Do NOT rescale the whole character or move/repaint the body. Change ONLY the head/skull/face/glasses size and seamlessly repaint the neck/hair junction. Match the skull-to-chin height of image2 (about 250 pixels), same adult-stylized face, same glasses, neutral dark hair and image1 hair flow. Neck stays naturally inside existing collar, no pasted edge or gap. Keep the exact body and clothing colors. Maintain eye center approximately at the specified target so animation alignment is stable. Keep all original transparency. One complete figure, no labels. REDUCE oversized head by about 16%, skull/face/glasses together. Keep neck base fixed, eye center approximately (981,248). Do not merely alter hair volume.

## 第7帧提示词

Precise localized animation consistency edit. Image1 is the TARGET whole running sprite, image2 supplies ONLY the correct HEAD SIZE. Preserve image1's entire running pose, both arms/hands, torso/jacket, hips, legs and shoes, size and position on the exact 1536x1024 transparent canvas. Do NOT rescale the whole character or move/repaint the body. Change ONLY the head/skull/face/glasses size and seamlessly repaint the neck/hair junction. Match the skull-to-chin height of image2 (about 250 pixels), same adult-stylized face, same glasses, neutral dark hair and image1 hair flow. Neck stays naturally inside existing collar, no pasted edge or gap. Keep the exact body and clothing colors. Maintain eye center approximately at the specified target so animation alignment is stable. Keep all original transparency. One complete figure, no labels. ENLARGE slightly undersized head by about 10%, skull/face/glasses together, eye center approximately (991,173). Keep all head/hair inside top edge with clear margin, do not enlarge body.

## 第8帧提示词

Precise localized animation consistency edit. Image1 is the TARGET whole running sprite, image2 supplies ONLY the correct HEAD SIZE. Preserve image1's entire running pose, both arms/hands, torso/jacket, hips, legs and shoes, size and position on the exact 1536x1024 transparent canvas. Do NOT rescale the whole character or move/repaint the body. Change ONLY the head/skull/face/glasses size and seamlessly repaint the neck/hair junction. Match the skull-to-chin height of image2 (about 250 pixels), same adult-stylized face, same glasses, neutral dark hair and image1 hair flow. Neck stays naturally inside existing collar, no pasted edge or gap. Keep the exact body and clothing colors. Maintain eye center approximately at the specified target so animation alignment is stable. Keep all original transparency. One complete figure, no labels. REDUCE oversized head by about 14%, skull/face/glasses together. Keep neck base fixed, eye center approximately (1077,238). Do not merely alter hair volume.

