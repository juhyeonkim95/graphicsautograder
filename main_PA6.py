import os
from html2image import Html2Image
import re
import cv2
import numpy as np
from glob import glob
import pandas as pd
from itertools import product
from tqdm import trange, tqdm
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")

IMAGE_TOP_MARGIN = 64


def auto_grade(**kwargs):
    output_folder = kwargs.get("output_folder")
    image_output_folder = kwargs.get("image_output_folder")
    solution_file_name = kwargs.get("solution_file_name")

    target_task = kwargs.get("target_task", 1)

    if target_task < 10:
        target_task_name = "task%d-ch%d" % (target_task, target_task + 3)
    else:
        target_task_name = "task%d" % target_task
    # Grade
    html_file_list_temp = glob("%s\\**\\%s.html" % (output_folder, target_task_name), recursive=True)

    student_names = []
    html_file_list = []

    for html_file_name in html_file_list_temp:
        student_name = html_file_name.split("\\")[9]
        if student_name not in student_names:
            student_names.append(student_name)
            html_file_list.append(html_file_name)

    target_times = [1.0]

    def run_export(target_time_idx):
        for i in trange(len(html_file_list)):
            html_file_name = html_file_list[i]
            student_name = student_names[i]
            try:
                with open(html_file_name, 'r', encoding='utf-8') as html_file:
                    html_as_string = html_file.read()
            except:
                try:
                    with open(html_file_name, 'r', encoding='cp949') as html_file:
                        html_as_string = html_file.read()
                except:
                    print(student_name)
                    continue

            target_time = target_times[target_time_idx]
            change_list = [
                ("buffer.Shader.uniforms['iTime'].value = time;", "buffer.Shader.uniforms['iTime'].value = %f;" % target_time),
                ("buffer.Shader.uniforms['time'].value = time;", "buffer.Shader.uniforms['time'].value = %f;" % target_time),
            ]

            new_html_string = html_as_string
            for v in change_list:
                orig_str, new_str = v
                new_html_string = new_html_string.replace(orig_str, new_str)

            new_html_file_name = html_file_name.replace(target_task_name, "%s_temp" % target_task_name)
            with open(new_html_file_name, 'w', encoding='utf-8') as html_file:  # r to open file in READ mode
                html_file.write(new_html_string)

            output_path = os.path.join(image_output_folder, "task%d" % target_task)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            hti = Html2Image()
            hti.output_path = output_path
            hti.screenshot(
                html_file=new_html_file_name, save_as='%s.png' % student_name,
                size=[(640, 360)]
            )

    threshold = kwargs.get("error_threshold")
    threshold2 = kwargs.get("error_threshold2")

    def run_error():
        data = {}
        task_folder = "task%d" % target_task
        # root = os.path.join(image_output_folder, task_folder)
        # dirlist = [item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item))]
        # student_names = dirlist

        error_sum = 0
        score_sum = 0
        for i in range(len(target_times)):
            # file_name = "%d.png" % i

            solution_image = cv2.imread(
                os.path.join(image_output_folder, task_folder, solution_file_name+".png"))
            solution_image = np.asarray(solution_image, dtype=np.float32)
            solution_image /= 255.0
            #solution_image /= solution_image.sum()
            errors = []
            scores = []
            for student_name in student_names:
                image = cv2.imread(
                    os.path.join(image_output_folder, task_folder, student_name+".png"))
                image = np.asarray(image, dtype=np.float32)
                image /= 255.0

                error_image = (solution_image - image)
                error_image = error_image[IMAGE_TOP_MARGIN:, :, :]
                error = np.sqrt(np.mean(error_image * error_image))
                if error < threshold:
                    score = 1
                elif error < threshold2:
                    score = 0.5
                else:
                    score = 0
                errors.append(error)
                scores.append(score)
            errors = np.asarray(errors)
            error_sum = errors + error_sum
            scores = np.asarray(scores)
            score_sum = scores + score_sum
        data["error"] = error_sum / len(target_times)
        data["score"] = score_sum / len(target_times)
        df = pd.DataFrame().from_dict(data)
        df.insert(0, "Name", student_names, True)
        df.to_csv("%s/%s.csv" % (image_output_folder, task_folder), index=False)

    run_export(0)
    run_error()


if __name__ == "__main__":
    common_configs = {
        "output_folder": "C:\\Users\\cjdek\\Desktop\\Course\\2024winter\\computer graphics\\grading\\PA6_test",
        "solution_file_name": "zzz_solution",
        "image_output_folder": "outputs/PA6"
    }

    auto_grade(target_task=1, error_threshold=5e-2, error_threshold2=1e-1, **common_configs)
    auto_grade(target_task=2, error_threshold=5e-2, error_threshold2=1e-1, **common_configs)
    auto_grade(target_task=3, error_threshold=3e-2, error_threshold2=1e-1, **common_configs)
    auto_grade(target_task=4, error_threshold=3e-2, error_threshold2=1e-1, **common_configs)
    auto_grade(target_task=5, error_threshold=5e-2, error_threshold2=1e-1, **common_configs)
    auto_grade(target_task=6, error_threshold=3e-2, error_threshold2=1e-1, **common_configs) # slow!
    auto_grade(target_task=7, error_threshold=3e-2, error_threshold2=1e-1, **common_configs)

    # seems to now work after p8
    #auto_grade(target_task=8, error_threshold=3e-2, error_threshold2=1e-1)
    #auto_grade(target_task=9, error_threshold=3e-2, error_threshold2=1e-1)
    #auto_grade(target_task=10, error_threshold=5e-2, error_threshold2=1e-1)
    #auto_grade(target_task=11, error_threshold=5e-2, error_threshold2=1e-1)
    #auto_grade(target_task=12, error_threshold=5e-2, error_threshold2=1e-1)

