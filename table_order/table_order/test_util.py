from ament_index_python.packages import get_package_share_directory
import os


def get_package_dir(package_name):
    try:
        return os.path.join(
            get_package_share_directory(package_name),
            "..",
            "..",
            "src",
            "table_order",
            "table_order",
        )
    except:
        return None
