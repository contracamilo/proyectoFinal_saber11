# Guía de contribución

El profesor evalúa **solo la rama `develop`** y verifica el aporte de cada integrante por sus commits en su rama individual. Si la rama no existe con el nombre correcto, se asume que el integrante no hizo la actividad.

## Ramas

| Rama | Uso |
|---|---|
| `main` | Rama inicial; no se trabaja aquí. |
| `develop` | Consolidación del proyecto. **Rama que revisa el profesor.** Solo recibe merges de PRs. |
| `dev_crivera52` | Camilo Rivera |
| `dev_dcharry55` | Daniel Charry |
| `dev_rcaicedo05` | Richard Caicedo |

## Configuración inicial (una sola vez)

```bash
git clone https://github.com/contracamilo/proyectoFinal_saber11.git
cd proyectoFinal_saber11
git config user.name "Tu Nombre"
git config user.email "correo-asociado-a-tu-github@..."   # si no coincide, GitHub no te atribuye los commits
git switch dev_<tuUsuario>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .            # permite "import saber11" desde notebooks, scripts y tests
```

Las interfaces que cada capa debe respetar están en [`docs/arquitectura/contratos.md`](docs/arquitectura/contratos.md).

## Ciclo de trabajo

```bash
git switch dev_<tuUsuario>
git pull origin develop                 # sincronizar antes de empezar
# ... cambios ...
git add <archivos>
git commit -m "feat(data): descarga paginada desde datos.gov.co"
git push origin dev_<tuUsuario>
```

Luego abrir un Pull Request `dev_<tuUsuario>` → `develop` con **Camilo (`contracamilo`) como reviewer**. Camilo revisa, aprueba y hace el merge con **"Create a merge commit"** (el squash y el rebase están desactivados porque borran la autoría individual de los commits).

**Nunca borres tu rama** después del merge: el profesor la busca para verificar tu aporte.

## Convención de commits

`<tipo>(<capa>): <descripción en presente>`

- Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
- Capas: `data`, `features`, `model`, `api`, `docs`, `arch`.

Ejemplos:
- `feat(model): agrega baseline DummyClassifier`
- `docs(adr): ADR-002 selección del modelo`
- `test(api): valida respuesta de /predict`

Commits pequeños y frecuentes: el profesor penaliza repositorios con un solo commit por persona.

## Reglas
- Nunca hacer commit directo en `develop` ni en `main`.
- No subir datos crudos ni el `.db` (están en `.gitignore`); sí subir figuras y reportes.
- Cada PR a `develop` o `main` necesita la aprobación de Camilo (`.github/CODEOWNERS`).

## Reglas configuradas en GitHub

| Ramas | Regla |
|---|---|
| `develop`, `main` | Solo se modifican por Pull Request con 1 aprobación del code owner (Camilo). Un nuevo push invalida la aprobación anterior. Sin force push ni borrado. Solo el admin puede saltarse la revisión, y únicamente desde un PR. |
| `dev_*` | No se pueden borrar ni reescribir con force push: son la evidencia del trabajo de cada integrante. |
| Repositorio | Solo "Create a merge commit"; squash y rebase desactivados. |
