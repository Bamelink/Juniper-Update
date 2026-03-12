"""Read pre/post JSON logs produced by the playbook and render a combined Markdown report."""
import json
import glob
import os

def load_logs(pattern):
    data = {}
    for path in glob.glob(pattern):
        with open(path) as f:
            host = os.path.basename(path).split('_')[0]
            data.setdefault(host, {})
            if '_pre' in path:
                data[host]['pre'] = json.load(f)
            elif '_post' in path:
                data[host]['post'] = json.load(f)
            elif '_version' in path:
                data[host]['version'] = json.load(f)
    return data


def render_markdown(logs):
    lines = ['# Juniper Upgrade Details\n']
    for host, parts in logs.items():
        lines.append(f'## {host}\n')
        for phase in ('pre', 'post'):
            lines.append(f'### {phase.capitalize()} check\n')
            content = parts.get(phase, {})
            # surround JSON with fenced code block markers
            lines.append("```\n" + json.dumps(content, indent=2) + "\n```")
    return '\n'.join(lines)


def main():
    logs = load_logs('logs/*_*.json')
    md = render_markdown(logs)
    outpath = 'upgrade-details.md'
    with open(outpath, 'w') as f:
        f.write(md)
    print(f"Wrote detailed report to {outpath}")

if __name__ == '__main__':
    main()
