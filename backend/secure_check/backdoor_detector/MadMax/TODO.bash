cd output
rm -rf ./*
# compile
../solc4.26 --bin-runtime ../examples/loop.sol | tail -n 1 > ../examples/loop.hex
../bin/decompile -n -v -c "remove_unreachable=1" -g ../examples/loop.html ../examples/loop.hex
# datalog analysis
../bin/analyze.sh ../examples/loop.hex ../tools/bulk_analyser/mySpec.dl