from setuptools import find_packages, setup

package_name = "table_order"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ynu",
    maintainer_email="ynu@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            # 'kitchen = table_order.order_page:main',
            "kitchen = table_order.kitchen_gui_main:main",
            "table = table_order.table:main",
            "robot = table_order.robot_gui:main",
        ],
    },
)
