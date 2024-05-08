from anthropic import Anthropic
import os
from devon_agent.agent.clients.client import ClaudeSonnet
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.create_diff import generate_unified_diff2
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon_swe_bench_experimental.swebenchenv.environment.unified_diff.utils import MultiFileDiff2, construct_versions_from_diff_hunk, match_stripped_lines
def apply_diff2(multi_file_diff: MultiFileDiff2, src: str):
        for file_diff in multi_file_diff.files:

            src_content = src
            src_lines = [(i, line) for i, line in enumerate(src_content.splitlines())]

            tgt_lines = list(src_lines)

            for hunk in file_diff.hunks:
                old_lines, new_lines = construct_versions_from_diff_hunk(hunk)
                src_start, src_end = match_stripped_lines(src_lines, old_lines)

                i = 0
                while i < len(tgt_lines):
                    if tgt_lines[i][0] == src_start:
                        j = 0
                        while i + j < len(tgt_lines) and tgt_lines[i+j][0] != src_end:
                            j += 1
                        
                        tgt_lines[i:i+j+1] = [(-1, line) for line in new_lines]
                        break
                        
                    i += 1
            
            new_code = "\n".join([entry[1] for entry in list(tgt_lines)])
            return new_code
i = """import django
from django import forms

class MyForm(forms.Form):
    url = forms.URLField()

def reproduce_issue():
    form = MyForm(data={'url': '////]@N.AN'})
    try:
        form.fields['url'].clean('////]@N.AN')
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    django.conf.settings.configure(
        DEBUG=True,
        SECRET_KEY='not-a-real-secret-key',
        ROOT_URLCONF='django__django.urls',
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'db.sqlite3',
            }
        },
        USE_I18N=True,
    )
    reproduce_issue()"""

code = """import django
from django import forms

class MyForm(forms.Form):
    url = forms.URLField()

def reproduce_issue():
    form = MyForm(data={'url': '////]@N.AN'})
    try:
        form.fields['url'].clean('////]@N.AN')
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reproduce_issue()"""

api_key=os.environ.get("ANTHROPIC_API_KEY")
anthrpoic_client = Anthropic(api_key=api_key)
diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system, max_tokens=4096)
thought = "It seems we cannot configure Django settings directly in the terminal. Let's modify the reproduce_issue.py script to configure the settings before running the code."
output = generate_unified_diff2(client=diff_model, thought=thought, input_diff=i, file_tree="", code={"reproduce_issue.py": code}, files={})
new_code = apply_diff2(output, code)
print(new_code)