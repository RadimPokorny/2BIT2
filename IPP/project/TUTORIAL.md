docker build --target check -t ipp-check .
docker run -it --name ipp-env -v "${PWD}:/src" ipp-check