from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Evidence Scheduling', version='0.1.4.2',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        evidence = evidence
    """,
    package_data={'evidence': ['templates/*.html']},
    author = "Doychin Atanasov",
    author_email = "doychin@inv.bg",
    description = "Evidence based scheduler",
    license = "GPL",
    url = "http://github.com/ironsmile/evidencetracplugin",
)
    