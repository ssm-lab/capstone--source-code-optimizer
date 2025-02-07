import math
print(math.isclose(20, 100))

def process_local_call(data_value1, data_value2, data_item1, data_item2, 
    config_path, config_setting, config_option, config_env):
    return (data_value1 * data_value2 - data_item1 * data_item2 + 
        config_path * config_setting - config_option * config_env)


def process_data(data_value1, data_value2, data_item1, data_item2,
    config_path, config_setting, config_option, config_env):
    return (data_value1 + data_value2 + data_item1) * (data_item2 + config_path
        ) - (config_setting + config_option + config_env)


def process_extra(data_record1, data_record2, data_result1, data_result2,
    config_file, config_mode, config_param, config_directory):
    return data_record1 - data_record2 + (data_result1 - data_result2) * (
        config_file - config_mode) + (config_param - config_directory)


class Helper:

    def process_class_data(self, data_input1, data_input2, data_output1,
        data_output2, config_file, config_user, config_theme, config_env):
        return (data_input1 * data_input2 + data_output1 * data_output2 - 
            config_file * config_user + config_theme * config_env)

    def process_more_class_data(self, data_record1, data_record2,
        data_item1, data_item2, config_log, config_cache, config_timeout,
        config_profile):
        return data_record1 + data_record2 - (data_item1 + data_item2) + (
            config_log + config_cache) - (config_timeout + config_profile)


def main():
    local_result = process_local_call(1, 2, 3, 4, 3, 2, 3, 5)
    print(local_result)


if __name__ == '__main__':
    main()


