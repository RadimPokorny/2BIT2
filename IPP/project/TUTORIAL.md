# 1. Make a build for the Python check
docker build --target check -t ipp-check .

# 2. Make a build for the PHP tester
docker build --target test -t ipp-test .

# 3. Run the images to test and check at the same time
docker run -it --rm -v "${PWD}/int:/src/int" -v "${PWD}/tester:/src/tester" ipp-check