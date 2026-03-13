# Docker Setup

## 1. Make a build for the Python check
`docker build --target check -t ipp-check .`

## 2. Make a build for the PHP tester
`docker build --target test -t ipp-test .`

## 3. Run the images to test and check at the same time
`docker run -it --rm -v "${PWD}:/src" ipp-check`

---
# Run the Interpreter manually

## 1. Use the SOL2XML converter
`python3 sol_to_xml.py example.sol > example.xml`

## 2. Export the Python path into the environment
`export PYTHONPATH=$PYTHONPATH:$(pwd)/int/src`

## 3. Run the interpreter and get the result in STD
`python3 int/src/solint.py --source example.xml`

---

# Run the tester

## 1. Move to the right directory
`cd /src/tester`

## 2. Run tester and save the report 
`php src/tester.php ../tests --output report.json`


