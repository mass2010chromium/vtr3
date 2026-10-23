docker build -t vtr3 \
  --build-arg USERID=$(id -u) \
  --build-arg GROUPID=$(id -g) \
  --build-arg USERNAME=$(whoami) \
  --build-arg HOMEDIR=${HOME} \
  --build-arg CUDA_ARCH="86" .
