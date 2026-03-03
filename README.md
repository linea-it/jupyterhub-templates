# jupyterhub-templates

Extensão JupyterLab que adiciona o menu **Templates** na barra superior. O diretório de templates é definido por **`JUPYTER_TEMPLATES_DIR`** (padrão: `/opt/notebook-templates`). Cada subpasta vira um submenu; cada notebook `.ipynb` vira um item que, ao clicar, cria e abre uma cópia do template.

**O wheel não inclui templates.** Na instalação, copie os seus `.ipynb` para um diretório (ex.: `/opt/notebook-templates`) e defina `JUPYTER_TEMPLATES_DIR` para esse path.

---

## Instalação

### Via pip (wheel)

O `.whl` inclui **servidor** e **labextension** (menu). Os [releases do GitHub](https://github.com/linea-it/jupyterhub-templates/releases) gerados pelo CI contêm o wheel. Build manual: secção "Build local" abaixo.

```bash
pip install templates_menu-0.1.0-py3-none-any.whl
```

**Labextension (menu na barra):** O wheel instala a extensão em `$PREFIX/share/jupyter/labextensions/templates-menu-lab/`. Se noutro ambiente o menu não aparecer, copie a pasta para `$PREFIX/share/jupyter/labextensions/` ou use `jupyter labextension install <caminho>`.

**JupyterLab 4:** Depois de instalar o wheel, é **obrigatório** rodar **`jupyter lab build`** (exige **Node.js** no ambiente). Sem isso o menu pode não aparecer.

Ative a extensão de servidor (uma vez). Exemplo em `jupyter_server_config.d`:

```json
{
  "ServerApp": {
    "jpserver_extensions": {
      "templates_menu": true
    }
  }
}
```

**Templates:** Defina **`JUPYTER_TEMPLATES_DIR`** para o diretório onde estão os `.ipynb` (ex.: `export JUPYTER_TEMPLATES_DIR=/opt/notebook-templates`). O wheel não inclui templates; copie os ficheiros na instalação (ver exemplo Docker abaixo).

---

## Uso na imagem Docker

Copie os templates para um diretório na imagem, instale o wheel e defina `JUPYTER_TEMPLATES_DIR`. Exemplo (ajuste `WHEEL_URL` e o path dos templates):

```dockerfile
ARG WHEEL_URL=https://github.com/linea-it/jupyterhub-templates/releases/download/v0.1.0/templates_menu-0.1.0-py3-none-any.whl

RUN mkdir -p /opt/notebook-templates
COPY linea-templates/ /opt/notebook-templates/
RUN chown -R jovyan:users /opt/notebook-templates

# Instala a extensão de Templates via wheel do release
RUN curl -f -L -o /tmp/templates_menu-0.1.0-py3-none-any.whl "${WHEEL_URL}" \
    && python3 -c "import zipfile; zipfile.ZipFile('/tmp/templates_menu-0.1.0-py3-none-any.whl')" \
    || (echo "Downloaded file is not a valid wheel. Confira WHEEL_URL e se o release/asset existem e são públicos." && exit 1)
USER jovyan
RUN pip install --no-cache-dir /tmp/templates_menu-0.1.0-py3-none-any.whl
USER root
RUN printf '%s\n' '{' '  "ServerApp": {' '    "jpserver_extensions": {' '      "templates_menu": true' '    }' '  }' '}' > /opt/conda/etc/jupyter/jupyter_server_config.d/templates_menu.json

ENV JUPYTER_TEMPLATES_DIR=/opt/notebook-templates
```

Rode **`jupyter lab build`** após o `pip install` se o ambiente tiver Node.js (recomendado para JupyterLab 4).

---

## Build local (gerar o .whl)

Requer: **Python 3.9+**, **Node.js**, **npm**. Instale antes: `pip install build hatchling hatch-jupyter-builder jupyterlab`.

```bash
cd templates_menu_lab && npm install && npm run build:lib && jupyter labextension build . && cd ..
python -m build --wheel --outdir dist/ --no-isolation
```

O arquivo `.whl` fica em `dist/`. O wheel inclui apenas a **labextension** em `share/jupyter/labextensions/templates-menu-lab/` (schemas, static JS, package.json). Templates não vêm no wheel; na instalação use `JUPYTER_TEMPLATES_DIR` apontando para um diretório local.

**Segurança (npm audit):** O `npm audit` em `templates_menu_lab` pode reportar vulnerabilidades em **devDependencies** (webpack, @jupyterlab/builder, etc.). Essas dependências são só para build; **não entram no .whl** distribuído. Para zerar o audit seria necessário Node 20+ (ex.: `serialize-javascript@7.0.3`) ou atualizações do próprio JupyterLab.

---

## Publicar um release (GitHub)

1. Atualize o campo `version` em `pyproject.toml`.
2. No GitHub: **Releases** → **Create a new release**; crie a tag (ex.: `v0.1.0`) e publique.
3. O workflow **Build and attach .whl to Release** gera o `.whl` em CI e anexa aos Assets do release.
4. Baixe o `.whl` na página do release para usar na imagem ou com `pip install`.

---

## Estrutura do repositório

| Pasta / arquivo | Descrição |
|-----------------|-----------|
| `templates_menu/` | Extensão de **servidor** (Python): API `/templates-menu/templates` e `/templates-menu/create`. |
| `templates_menu_lab/` | Extensão de **frontend** (TypeScript): menu "Templates" e submenus na interface. |
| `templates/` | Exemplos de notebooks no repositório (não empacotados no wheel). Na instalação, use `JUPYTER_TEMPLATES_DIR` para um diretório local com os seus `.ipynb`. |
| `.github/workflows/release.yml` | CI: ao publicar um release, gera o `.whl` e anexa ao release. |

Este repositório não contém o Dockerfile da imagem final. A imagem que usa a extensão instala o `.whl` (do release ou do build local) e copia os templates para o diretório definido por `JUPYTER_TEMPLATES_DIR` (ex.: `/opt/notebook-templates`).
