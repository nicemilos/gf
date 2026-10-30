# 小雅屏幕边缘探头（本地开发）

使用内置 imagegen，以已确认的站立图保留角色身份；用户提供的扶墙探头图片仅作为姿势参考。背景为真实透明，墙由屏幕外侧自然遮挡，不额外绘制墙面。

Q版与原版分别生成，保留各自的头身比例。右侧通过运行时镜像实现，避免两侧身份和衣服变化。运行时裁去透明外边距，不修改生成图片的像素。

拖动时用角色的虚拟中心判断是否进入边缘，探头窗口固定在屏幕内，因此仍可被抓住拖回。退出阈值略大于进入阈值，减少边缘闪烁。显示器相连的位置不当作墙；上下边缘不触发。

窗口几何位置一次提交：先计算跑步宽度、虚拟位置及探头吸附位置，再调用一次 setGeometry。禁止先移到屏幕外再拉回；松手缩回宽度时也直接使用最终边缘位置。跑步朝向取鼠标实际移动方向，不取鼠标与吸附窗口的距离。`test_pet_drag.py` 监听真实 QWidget 的 moveEvent，覆盖两种形象、两侧进入/连续移动/松手/拖回，防止恢复瞬时跳动。

右键和托盘菜单按状态切换“躲起来/快回来”。自动躲藏选择距离最近的可探头边缘，忽略相连显示器的接缝；用跑步动作和位置动画靠近边缘，结束后一次切换为探头。自动返回优先恢复躲藏前的位置，手动拖出的则回到当前屏幕内、离边缘留有距离的位置。动画途中允许召回和手动拖拽打断；托盘菜单每次打开都刷新状态。

资源：`assets/q-peek.png`、`assets/natural-peek.png`。

## Q版生成提示词

Use case: identity-preserve. Asset type: transparent desktop pet sprite. Input image 1 is Xiaoya's approved Q-version identity and exact rendering style. Input image 2 is ONLY a pose reference: shyly peeking around a VERTICAL wall edge from the LEFT side of the screen, head tilted into visible space on the RIGHT, fingers gripping that edge. Create one single complete integrated drawing of Xiaoya in this peeking pose. Preserve her very dark almost-black wavy long hair, large brown eyes, round fine gold/brown glasses, tiny mouth and nose, cream ivory puffer jacket and exaggerated Q big-head proportions. Show a curious gentle expression, most of her head and one shoulder plus partial upper torso and a small hand, remaining body hidden behind the imaginary wall to the left. The occlusion boundary is a straight vertical line at x=15% of canvas width, with character extending to the right from there. Hand grips the invisible vertical edge. NO actual wall or line is drawn: ALL surroundings and area left of the clipping boundary are truly transparent. Head leans right around this imaginary edge; not a standing full figure, no legs. Keep all visible head/hair/hand inside frame with small padding top/right/bottom, no text, no UI, no cat ears, no warm brown/orange hair recoloring. Portrait 2:3 canvas. Transparent RGBA background, no painted checkerboard, no shadows/background glow. This will be aligned to a monitor's left edge, mirrored in app for the right edge.

## 原版生成提示词

Use case: identity-preserve. Asset type: transparent desktop pet peeking sprite. Image 1 is the ORIGINAL / natural-proportioned Xiaoya identity reference. Image 2 is ONLY the desired peeking pose and clipping composition, and is the Q version, NOT the target head/body proportions. Redraw image 1 in image 2's peeking pose: peeking out toward RIGHT from behind an invisible vertical wall on the LEFT, tilted curious head, one small hand holding edge, one shoulder and partial torso visible, most body hidden. Maintain original/natural version's face, smaller eyes and smaller head relative to torso, longer adult-proportioned shoulders/upper body; clearly less chibi than image 2. Her wavy long almost-black dark hair, round gold/brown glasses, ivory puffer jacket and gentle expression must match image 1. Do not make hair lighter brown. Keep integrated anatomy and collar attached to head. The invisible wall boundary runs vertically at 15% of image width; body cut by this boundary, hand wraps around it; NO wall/line actually drawn, all background and area left of edge truly transparent. No legs; partial bust, not entire standing body. Small transparent margin around top/right/bottom, portrait 2:3. Transparent RGBA background, no text, no shadow/glow, no extra objects. Same fine detailed anime rendering as identity reference. This sprite will be aligned to monitor edge and mirrored for opposite screen side.
