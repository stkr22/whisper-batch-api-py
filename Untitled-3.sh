git clone https://github.com/OpenNMT/CTranslate2.git ./ctranslate2 && \
cd ./ctranslate2 && \
git checkout 383d063 && git submodule update --init --recursive && \
cmake -Bbuild_folder -DWITH_MKL=OFF -DOPENMP_RUNTIME=NONE -DWITH_CUDA=ON -DWITH_CUDNN=ON && \
cmake --build build_folder && \
cd build_folder && \
make install
