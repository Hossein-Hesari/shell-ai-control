figlet shell controler

echo " ------"
echo "RUN Project "
echo " ------"



echo "create Virtual env in Python ..."

python3 -m venv .venv 

source .venv/bin/activate.fish

echo "Virtual env is Created ..."


echo "Run Main of Project"

python3 controler.py
