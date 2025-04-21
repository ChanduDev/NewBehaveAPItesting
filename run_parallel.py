import os
import sys
import glob
import shutil
import uuid
import argparse
import multiprocessing
from subprocess import call

def run_feature_file(args):
    feature_file, tags, test_env, output_dir = args
    cmd = ["behave", feature_file]
    if tags:
        cmd.append(f"--tags={tags}")
    if test_env:
        cmd.append(f"-D TEST_ENV={test_env}")
    if output_dir:
        cmd.append(f"--no-capture")
        cmd.append(f"--no-capture-stderr")
        cmd.append(f"-D allure_results_dir={output_dir}")

    cmd_str = " ".join(cmd)
    print(f"Running: {cmd_str}")
    return call(cmd_str, shell=True)

def discover_feature_files(base_dir="features"):
    return glob.glob(os.path.join(base_dir, "**", "*.feature"), recursive=True)

def merge_allure_results(base_dir):
    merged_dir = os.path.join(base_dir, f"merged_{uuid.uuid4().hex[:6]}")
    os.makedirs(merged_dir, exist_ok=True)
    for subdir in os.listdir(base_dir):
        sub_path = os.path.join(base_dir, subdir)
        if os.path.isdir(sub_path):
            for file in os.listdir(sub_path):
                shutil.copy2(os.path.join(sub_path, file), os.path.join(merged_dir, file))
    print(f"Allure results merged to: {merged_dir}")
    return merged_dir

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tags', type=str, help='Run scenarios with specific tags only')
    parser.add_argument('--env', type=str, default='dev', help='Set the environment profile to run')
    parser.add_argument('--allure-dir', type=str, default='reports/allure-results-parallel', help='Base directory for Allure result outputs')
    args = parser.parse_args()

    feature_files = discover_feature_files()
    print(f"Discovered {len(feature_files)} feature files.")

    task_args = [
        (
            file,
            args.tags,
            args.env,
            os.path.join(args.allure_dir, os.path.splitext(os.path.basename(file))[0])
        ) for file in feature_files
    ]

    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        results = pool.map(run_feature_file, task_args)

    failed = [r for r in results if r != 0]
    if failed:
        print(f"{len(failed)} test(s) failed.")
        sys.exit(1)
    else:
        print("All tests passed successfully.")

    merged_dir = merge_allure_results(args.allure_dir)
    os.system(f"allure generate {merged_dir} --clean -o reports/allure-report")
    print("Allure HTML report generated at: reports/allure-report")

if __name__ == "__main__":
    main()