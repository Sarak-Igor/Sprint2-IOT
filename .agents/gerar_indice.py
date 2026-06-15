import os
import re
from pathlib import Path

def extrair_description(skill_md_path):
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'^description:\s*(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return "Descrição não encontrada."

def main():
    base_dir = Path(__file__).parent
    skills_dir = base_dir / "skills"
    commands_dir = base_dir / "commands"
    index_file = base_dir / "index.md"
    
    lines = ["# Catálogo de Inteligência Local (.agents)\n"]
    lines.append("Este arquivo é auto-gerado. Ele lista todas as regras de negócio deste projeto para as IAs.\n")
    
    lines.append("## Skills\n")
    if skills_dir.exists():
        for skill_folder in sorted(os.listdir(skills_dir)):
            skill_md = skills_dir / skill_folder / "SKILL.md"
            if skill_md.exists():
                desc = extrair_description(skill_md)
                lines.append(f"- **{skill_folder}**: {desc}\n  - *Caminho*: `.agents/skills/{skill_folder}/SKILL.md`\n")
                
    lines.append("\n## Comandos Customizados\n")
    if commands_dir.exists():
        for cmd_file in sorted(os.listdir(commands_dir)):
            if cmd_file.endswith(".md"):
                cmd_name = "/" + cmd_file[:-3]
                lines.append(f"- **{cmd_name}**: `.agents/commands/{cmd_file}`\n")
                
    agents_dir = base_dir / "agents"
    lines.append("\n## Subagentes\n")
    if agents_dir.exists():
        for agent_file in sorted(os.listdir(agents_dir)):
            if agent_file.endswith(".md"):
                lines.append(f"- **{agent_file[:-3]}**: `.agents/agents/{agent_file}`\n")
                
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print("[OK] Índice gerado com sucesso em .agents/index.md")

if __name__ == "__main__":
    main()
