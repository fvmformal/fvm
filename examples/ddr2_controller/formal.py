from fvm import fvmframework
import requests
import os
import tarfile

fvm = fvmframework()

## The following code is used to download and extract the GRLIB IP Library
## The extracted files are then added to the FVM framework
## Feel free to remove/ignore this code if you already have the GRLIB IP Library extracted
# URL of the GRLIB IP Library page

def comment_vhdl_lines(file_path, line_numbers):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line_num in line_numbers:
        if 0 < line_num <= len(lines):
            lines[line_num - 1] = "-- " + lines[line_num - 1]  

    with open(file_path, 'w') as f:
        f.writelines(lines)

download_link = "https://download.gaisler.com/products/GRLIB/bin/grlib-gpl-2024.4-b4295.tar.gz"
file_name = os.path.basename(download_link)

# If the file already exists, skip downloading
if os.path.exists(file_name):
    print(f"The file {file_name} is already downloaded.")
else:
    print(f"Downloading: {download_link}")
    os.system(f"wget {download_link}")

# Extract if not already extracted
extracted_folder = file_name.replace(".tar.gz", "")
if not os.path.exists(extracted_folder):
    print(f"Extracting {file_name}...")
    with tarfile.open(file_name, "r:gz") as tar:
        tar.extractall(extracted_folder)
    print(f"Extracted to: {extracted_folder}")
else:
    print(f"The folder {extracted_folder} already exists, skipping extraction.")

comment_vhdl_lines(f"{extracted_folder}/{extracted_folder}/lib/gaisler/ddr/ddr2spax_ddr.vhd", [885, 886])

fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/config_types.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/config.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/version.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/stdlib/stdlib.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/amba/devices.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/grlib/amba/amba.vhd","grlib")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/gaisler/ddr/ddrpkg.vhd","gaisler")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/gaisler/ddr/ddrintpkg.vhd","gaisler")
fvm.add_vhdl_source(f"{extracted_folder}/{extracted_folder}/lib/gaisler/ddr/ddr2spax_ddr.vhd","gaisler")

fvm.add_psl_sources("examples/ddr2_controller/*.psl")

fvm.set_toplevel("gaisler.ddr2spax_ddr")
fvm.add_config("gaisler.ddr2spax_ddr", "ddr_width_16", {"ddrbits": 16})

fvm.skip('xverify')
fvm.skip('reachability')
fvm.skip('prove.formalcover')
#fvm.skip('prove.simcover')

fvm.run()
