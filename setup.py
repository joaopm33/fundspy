from setuptools import setup, Extension
with open('README.md') as f:
  long_description = f.read()
setup(
  name = 'fundspy',         # How you named your package folder (MyLib)
  packages = ['fundspy'],   # Chose the same as "name"
  version = '1.0',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Download brazillian investment funds and their benchmarks data from CVM and analyze their performance with pre-built functions.',   # Give a short description about your library
  long_description=long_description,
  long_description_content_type='text/markdown',  
  author = 'Joao Penido Monteiro',                   # Type in your name
  author_email = 'joaopm33@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/joaopm33/fundspy',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/joaopm33/fundspy/archive/refs/tags/v1.0.tar.gz',    # I explain this later on
  keywords = ['INVESTMENTS', 'FUNDS', 'FINANCE', 'INVESTMENT FUNDS', 'BRAZILIAN ASSETS', 'HEDGE FUNDS', 'MUTUAL FUNDS'],   # Keywords that define your package best
  install_requires=[
                    'requests==2.22.0',
                    'yahoofinancials==1.6',
                    'python-dateutil==2.8.1',
                    'pandas==1.0.5',
                    'numpy==1.19.3',
                    'tqdm==4.11.2',
                    'workalendar==10.3.0'
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',  
    'Intended Audience :: Education',
    'Intended Audience :: Financial and Insurance Industry',  
    'Topic :: Office/Business :: Financial :: Investment',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)