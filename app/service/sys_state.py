from model.sys_state import count_records

def get_image_process_count(lock_class):
    return count_records(lock_class)