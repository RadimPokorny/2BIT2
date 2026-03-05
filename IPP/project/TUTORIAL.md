docker start ipp-env
docker exec -it ipp-env /bin/bashdocker run -it --name ipp-env -v "${PWD}:/src" ipp-check