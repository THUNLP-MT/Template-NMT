import argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", help="", type=str, default="translations/all/all.en-fr.en.sgm")
args = parser.parse_args()

with open(f"{args.input_file}") as inp:
    with open(f"{args.input_file[0:-3]}txt", "w") as out:
        for line in inp:
            if "</seg>" in line:
                soup = BeautifulSoup(line, "lxml")
                tokens = soup.text.split()
                new_line = " ".join(tokens)

                out.write(f"{new_line}\n")