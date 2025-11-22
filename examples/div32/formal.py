from fvm import FvmFramework
import requests
import os
import tarfile

fvm = FvmFramework()

## The following code is used to download and extract the GRLIB IP Library
## The extracted files are then added to the FVM framework
## Feel free to remove/ignore this code if you already have the GRLIB IP Library extracted
# URL of the GRLIB IP Library page
download_link = "https://download.gaisler.com/products/GRLIB/bin/grlib-gpl-2024.4-b4295.tar.gz"
file_name = os.path.basename(download_link)

# If the file already exists, skip downloading
if os.path.exists(file_name):
    print(f"The file {file_name} is already downloaded.")
else:
    print(f"Downloading: {download_link}")
    os.system(f"curl -O {download_link}")

# Extract if not already extracted
extracted_folder = file_name.replace(".tar.gz", "")
if not os.path.exists(extracted_folder):
    print(f"Extracting {file_name}...")
    with tarfile.open(file_name, "r:gz") as tar:
        tar.extractall(extracted_folder)
    print(f"Extracted to: {extracted_folder}")
else:
    print(f"The folder {extracted_folder} already exists, skipping extraction.")

# Add the extracted VHDL sources to the FVM framework
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/config_types.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/config.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/version.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/stdlib.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/modgen/multlib.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/techmap/gencomp/gencomp.vhd","techmap")
fvm.add_vhdl_sources(f"{extracted_folder}/{extracted_folder}/lib/gaisler/arith/*.vhd","gaisler")
fvm.add_vhdl_source("examples/div32/div32_common.vhd", "gaisler")

fvm.add_psl_source("examples/div32/div32.psl", flavor="vhdl", library="gaisler")

fvm.set_toplevel("gaisler.div32")

fvm.skip('reachability')
fvm.allow_failure('xverify')
fvm.skip('prove.simcover')
fvm.set_coverage_goal('prove.formalcover', 50)
fvm.set_coverage_goal('prove.simcover', 0)
fvm.run()
