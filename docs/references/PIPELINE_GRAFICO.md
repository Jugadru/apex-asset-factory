# APEX Asset Factory — pipeline gráfico automatizado

Objetivo: permitir que um agente autorizado ou desenvolvedor execute a mesma cadeia repetível para criar, validar e preparar recursos originais. Blender headless + Python/bpy + Godot 4.7.2, glTF/GLB, PBR, LOD, captura e regressão. Não depende de abrir o Blender manualmente para cada tarefa; não instala agente permanente nem promete execução em segundo plano. A execução requer runtime, ferramentas e permissão de arquivos; revisão visual continua obrigatória.

1. Brief: tipo (carro, pista, garagem, cenário, textura, áudio), era, dimensões, orçamento de triângulos/texturas, referências e autoria. Carros: pivôs de rodas, esterço, DRS 2012, slots de pintura. Pistas: distância esportiva vs geometria visual, alinhamento com spline, pit lane e câmeras.
2. Ingestão: fontes locais explicitamente autorizadas; registrar SHA256, autor, URL, licença, direitos de redistribuição. CC0 não é presumido. Não extrair assets de jogos comerciais. Separar referências não licenciadas de produção.
3. Build: scripts bpy com seed e parâmetros versionados; modelos procedurais genéricos, UV, materiais PBR, normais, escala em metros, origem/pivôs, LODs e colisão visual quando necessária. Exportar GLB em staging. Sem alterar assets aprovados.
4. QA: inspeção de orçamento de geometria, materiais, texturas, nomes, pivôs, limites, arquivos faltantes e importação Godot; inspeção humana das capturas. Reusar tools/apex_lab_graphics.py e visual_regression_ab.py para comparação 2D/3D; não confundir captura com FPS. MultiMesh para cenário repetitivo após medir.
5. Promoção: revisão explícita de licença, arte, importação e regressão; só então mover para assets de produção em PR. Registrar versão, hash e rollback. Nunca sobrescrever automaticamente.

Esqueleto entregue: asset_jobs.example.json (job de demonstração bloqueado até aprovação de licença), tools/apex_foundation.py (validate e plan, sem tocar assets), tools/apex_blender_scaffold.py (gerador original de carro geométrico de teste, invocado explicitamente pelo Blender; não usa fontes externas). A criação de carros detalhados, auto-UV avançado, baking, LOD por qualidade, importação/capturas automáticas e promoção não está homologada. São as próximas etapas do pipeline, não falsos PASS.

Comandos:
```sh
python3 tools/apex_foundation.py validate
python3 tools/apex_foundation.py plan docs/references/asset_jobs.example.json
# Em diretório de staging novo, não assets de produção:
blender --background --factory-startup --python-exit-code 1 --python tools/apex_blender_scaffold.py -- --output /tmp/apex-demo.glb
```

A ferramenta de planejamento imprime JSON e não executa Blender, não baixa nada, não altera arquivos. O protótipo Blender cria uma geometria genérica original em um arquivo que não existe; requer versão com exportador glTF. Validar manualmente no Godot e registrar evidência; não importar automaticamente. Quando o ambiente de execução estiver disponível, conectar as etapas reais ao Lab, sem duplicá-lo.

## Execução opcional da prova de conceito

O orquestrador `tools/apex_asset_build.py` conecta um job original aprovado
ao Blender local e valida estruturalmente o GLB retornado. Um workspace
novo é obrigatório; nunca executa em assets de produção, nunca promove
arquivos. Só suporta o carro geométrico original neste incremento.

```sh
python3 tools/apex_asset_build.py docs/references/asset_jobs.original.example.json --blender /caminho/para/blender --workspace /tmp/apex-asset-demo-novo
```

Saídas: staging/demo-car-001.glb, log do Blender e report.json com SHA256,
orçamento de triângulos, status de exportação e QA pendente. Validação do
GLB limita-se a contêiner, JSON, recursos embutidos e contagem de primitivas
triangulares, não comprova fidelidade de modelo, texturas, pivôs, importação,
nem renderização Godot. Jobs bloqueados não são executados. Não se
instala nenhum serviço e não se faz download. Os demais tipos de assets
continuam interfaces planejadas. A execução de teste deste orquestrador
está NOT_RUN até evidência.

## Asset Factory v0.1.0

Consulte [contrato, execução, evidências e roadmap](ASSET_FACTORY_010.md). O novo CLI em tools/asset_factory/build.py usa os contratos Foundation e Graphics Lab; mantém o scaffold anterior e não promove assets.
