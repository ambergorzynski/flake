import os 
import subprocess
from pathlib import Path

def run_cts(cts : Path,
    dawn : Path,
    mesa_vk_icd : Path,
    raw_output : Path) -> list[str]:

    env = os.environ.copy()
    if mesa_vk_icd != '':
        env["VK_ICD_FILENAMES"] = str(mesa_vk_icd)

    cmd = [f'{dawn}/tools/run',
        'run-cts',
        '--verbose',
        f'--bin={dawn}/out/Debug',
        f'--cts={str(cts)}',
        'webgpu:*']

    with open(raw_output,'wb') as f:
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        for line in p.stdout:
            print(line.decode('utf-8'))
            f.write(line)

def main():
    
    ### EDIT PATHS TO YOUR OWN LOCATIONS ###
    base = Path('/home/ubuntu/dev')
    cts = Path(base,'cts')
    dawn = Path(base, 'dawn')
    mesa_vk_icd = Path('/data/dev/mesa/build/install/share/vulkan/icd.d/lvp_icd.x86_64.json') # Set to '' to use your default driver
    output_dir = Path(base, 'data', 'cts_results', 'output_280525')
    ### END OF PATHS TO EDIT ###

    output_dir.mkdir(exist_ok=True)

    n_runs = 10

    output_raw = [Path(output_dir, f'output_raw_{i}.txt') for i in range(n_runs)]

    # Run the CTS multiple times and record output
    for i in range(n_runs):
        run_cts(cts, dawn, mesa_vk_icd, output_raw[i])

if __name__=="__main__":
    main()