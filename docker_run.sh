# Script for running VTR3 container in WSL with GPU passthrough (but bypass laptop GPU)
#
# Explained by Gemini:
# MESA_D3D12_DEFAULT_ADAPTER_NAME: For WSL configurations with both iGPU and discrete GPU,
#   this forces mesa to use the NVIDIA GPU instead of Intel iGPU.
# MESA_GL_VERSION / MESA_GLSL_VERSION: "WSL2's D3D12 driver artificially limits its reported
#   OpenGL profile, hiding the GL_ARB_copy_image extension. This forcefully overrides the profile,
#   tricking OGRE2 into seeing full OpenGL 4.6 compliance, which completely stops the
#   GL3PlusTextureGpu::copyTo crash." Gazebo was looking for some unimplemented feature
# QT_QPA_PLATFORM: Apparently X11 is more stable than Wayland/EGL for WSL2. Force usage of X11.
# OGRE_RTT_MODE: Maybe this can be omitted. May help with bugs in WSL2 Frame Buffer Objects
# LD_LIBRARY_PATH hacking: Use microsoft's GPU accelerated graphics before finding CPU/llvmpipe ones.
docker run -it --rm --name vtr3 --entrypoint bash \
  --gpus all \
  --privileged \
  --network=host \
  --ipc=host \
  -e USER_ID=$(id -u) \
  -e GROUP_ID=$(id -g) \
  -e USER_NAME=$(id -un) \
  -e DISPLAY=$DISPLAY \
  -e MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA \
  -e MESA_GL_VERSION_OVERRIDE=4.6 \
  -e MESA_GLSL_VERSION_OVERRIDE=460 \
  -e QT_QPA_PLATFORM=xcb \
  -e OGRE_RTT_MODE=Copy \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ${VTRROOT}:${VTRROOT}:rw \
  -v /usr/lib/wsl:/usr/lib/wsl \
  -v /dev:/dev\
  vtr3:latest \
  -c 'export LD_LIBRARY_PATH=/usr/lib/wsl/lib:${LD_LIBRARY_PATH}; bash'
