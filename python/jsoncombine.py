#!/usr/bin/python
import json
import argparse
import sys

##parser = argparse.ArgumentParser(description='Merges two or more json files into a single file.')

if __name__ == '__main__':
    result = {'bitmap':[]}
    for filename in sys.argv[1:]:
        with open(filename, "rb") as infile:
            input_data = json.load(infile)
            for bitmap in input_data['bitmap'] :
                result['bitmap'].append(bitmap)

    #merged_dict = {key: value for (key, value) in (dictA.items() + dictB.items())}
    
    with open("merged_file.json", "wb") as outfile:
         json.dump(result, outfile, sort_keys=False, indent=4, separators=(',', ': '))
