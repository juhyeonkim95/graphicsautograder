import os
from html2image import Html2Image
import re
import cv2
import numpy as np
from glob import glob
import pandas as pd
from itertools import product
from tqdm import trange, tqdm

IMAGE_TOP_MARGIN = 64
ERROR_EPSILON = 1

def auto_grade(**kwargs):
    output_folder = kwargs.get("output_folder")
    image_output_folder = kwargs.get("image_output_folder")
    solution_file_name = kwargs.get("solution_file_name")
    # target task id
    target_task = kwargs.get("target_task", 1)

    # find html file list
    html_file_list = glob("%s\\**\\main_task%d.html" % (output_folder, target_task), recursive=True)

    # define possible task modes
    task_1_modes = ["BOX", "LINE", "CYLINDER", "CYLINDER_TWO", "CONE", "CONE_TWO",
             "SPHERE_UNION", "SPHERE_INTERSECTION", "SPHERE_DIFFERENCE", "ROUNDED_BOX"]
    task_2_visualize_modes = ["VISUALIZE_RAY_DIR", "VISUALIZE_SDF_SLICE"]
    task_2_projection_modes = ["PROJECTION_ORTHOGRAPHIC", "PROJECTION_PERSPECTIVE"]
    task_3_ray_marching_modes = ["RAY_MARCHING", "SPHERE_TRACING"]
    task_3_visualize_modes = ["COST", "GRID"]
    task_3_shapes = ["SPHERE"]
    task_4_shade_modes = ["NORMAL", "DIFFUSE_POINT"]

    student_names = []

    for html_file_name in html_file_list:
        student_name = html_file_name.split("\\")[9]
        student_names.append(student_name)

    # change time?
    if target_task == 1:
        target_times = [1.0, 2.0, 3.0, 4.0]
    else:
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

            if target_task == 1:
                for mode in task_1_modes:
                    # int sdf_func = BOX;
                    new_html_string = re.sub("int sdf_func\s*=\s*.*;", "int sdf_func = %s;" % mode, new_html_string)

                    new_html_file_name = html_file_name.replace("main_task1", "main_task1_temp")
                    with open(new_html_file_name, 'w', encoding='utf-8') as html_file:  # r to open file in READ mode
                        html_file.write(new_html_string)

                    # print(new_html_string)
                    output_path = os.path.join(image_output_folder, "task1", student_name)
                    if not os.path.exists(output_path):
                        os.makedirs(output_path)

                    hti = Html2Image()
                    hti.output_path = output_path
                    hti.screenshot(
                        html_file=new_html_file_name, save_as='%s_%d.png' % (mode, target_time_idx),
                        size=[(640, 360)]
                    )
            elif target_task == 2:
                for visualize_func in task_2_visualize_modes:
                    for projection_func in task_2_projection_modes:
                        new_html_string = re.sub("int visualize_func\s*=\s*.*;", "int visualize_func = %s;" % visualize_func, new_html_string)
                        new_html_string = re.sub("int projection_func\s*=\s*.*;", "int projection_func = %s;" % projection_func, new_html_string)

                        new_html_file_name = html_file_name.replace("main_task2", "main_task2_temp")
                        with open(new_html_file_name, 'w', encoding='utf-8') as html_file:  # r to open file in READ mode
                            html_file.write(new_html_string)

                        # print(new_html_string)
                        output_path = os.path.join(image_output_folder, "task2", student_name)
                        if not os.path.exists(output_path):
                            os.makedirs(output_path)

                        hti = Html2Image()
                        hti.output_path = output_path
                        hti.screenshot(
                            html_file=new_html_file_name, save_as='%s_%s.png' % (visualize_func, projection_func)
                        )
            elif target_task == 3:
                configs = product(task_3_ray_marching_modes, task_3_visualize_modes, task_3_shapes)

                for config in tqdm(configs):
                    ray_marching_mode, visualize_mode, shape = config

                    new_html_string = re.sub("settings left_settings\s*=\s*.*;",
                                             "settings left_settings = settings(%s, %s, %s, TASK3, 0.35);" % (shape, visualize_mode, ray_marching_mode), new_html_string)
                    new_html_string = re.sub("settings right_settings\s*=\s*.*;",
                                             "settings right_settings = settings(%s, %s, %s, TASK3, 0.35);" % (shape, visualize_mode, ray_marching_mode), new_html_string)
                    if ray_marching_mode == "RAY_MARCHING":
                        new_html_string = re.sub("int cost_norm\s*=\s*.*;",
                                                 "int cost_norm = 2000;", new_html_string)
                    else:
                        new_html_string = re.sub("int cost_norm\s*=\s*.*;",
                                                 "int cost_norm = 200;", new_html_string)

                    new_html_file_name = html_file_name.replace("main_task3", "main_task3_temp")
                    with open(new_html_file_name, 'w', encoding='utf-8') as html_file:  # r to open file in READ mode
                        html_file.write(new_html_string)

                    output_path = os.path.join(image_output_folder, "task3", student_name)
                    if not os.path.exists(output_path):
                        os.makedirs(output_path)

                    hti = Html2Image()
                    hti.output_path = output_path
                    hti.screenshot(
                        html_file=new_html_file_name, save_as='%s_%s_%s.png' % (ray_marching_mode, visualize_mode, shape)
                    )
            elif target_task == 4:
                configs = product(task_4_shade_modes)
                directions = ["east", "west", "up", "down", "north", "south"]
                for direction in directions:
                    orig = "\"[^\"]*environment_maps/Uffizi_%s.jpg\"" % direction
                    new = "\"environment_maps/Uffizi_%s.jpg\"" % direction
                    new_html_string = re.sub(orig, new, new_html_string)

                for config in tqdm(configs):
                    shade_mode = config

                    new_html_string = re.sub("settings render_settings\s*=\s*.*;",
                                             "settings render_settings = settings(NONE, %s, NONE, TASK4, 0.35);" % (shade_mode), new_html_string)

                    new_html_file_name = html_file_name.replace("main_task4", "main_task4_temp")
                    with open(new_html_file_name, 'w', encoding='utf-8') as html_file:  # r to open file in READ mode
                        html_file.write(new_html_string)

                    # print(new_html_string)
                    output_path = os.path.join(image_output_folder, "task4", student_name)
                    if not os.path.exists(output_path):
                        os.makedirs(output_path)

                    hti = Html2Image()
                    hti.output_path = output_path
                    hti.screenshot(
                        html_file=new_html_file_name, save_as='%s.png' % shade_mode
                    )

    def run_error():
        data = {}
        task_folder = "task%d" % target_task
        root = os.path.join(image_output_folder, task_folder)
        dirlist = [item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item))]
        student_names = dirlist

        if target_task == 1:
            configs = product(task_1_modes)
        elif target_task == 2:
            configs = product(task_2_visualize_modes, task_2_projection_modes)
        elif target_task == 3:
            configs = product(task_3_ray_marching_modes, task_3_visualize_modes, task_3_shapes)
        elif target_task == 4:
            configs = product(task_4_shade_modes)

        for config in configs:
            error_sum = 0
            for i in range(len(target_times)):
                mode_name = "_".join(config)
                file_name = "%s.png" % mode_name
                if target_task == 1:
                    file_name = "%s_%d.png" % (mode_name, i)

                solution_image = cv2.imread(
                    os.path.join(image_output_folder, task_folder, solution_file_name, file_name))

                errors = []
                for student_name in student_names:
                    image = cv2.imread(
                        os.path.join(image_output_folder, task_folder, student_name, file_name))

                    error = (solution_image - image)
                    error = error[IMAGE_TOP_MARGIN:, :, :]
                    error = error * error
                    error = np.mean(error)
                    if error < ERROR_EPSILON:
                        error = 0
                    errors.append(error)
                errors = np.asarray(errors)
                error_sum = errors + error_sum
            data[mode_name] = error_sum / len(target_times)

        df = pd.DataFrame().from_dict(data)
        df.insert(0, "Name", student_names, True)
        df.to_csv("%s/%s/error.csv" % (image_output_folder, task_folder), index=False)

    for i in range(len(target_times)):
       run_export(i)

    run_error()


if __name__ == "__main__":

    common_configs = {
        "output_folder": "C:\\Users\\cjdek\\Desktop\\Course\\2024winter\\computer graphics\\grading\\PA5_test",
        "solution_file_name": "zzz_solution",
        "image_output_folder": "outputs/PA5"
    }
    auto_grade(target_task=1, **common_configs)
    auto_grade(target_task=2, **common_configs)
    auto_grade(target_task=3, **common_configs) #3 may not be perfect
    auto_grade(target_task=4, **common_configs) #4 may not be perfect
