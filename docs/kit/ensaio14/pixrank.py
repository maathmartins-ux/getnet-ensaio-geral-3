import sys

sys.path.insert(0, 'src')
from app.agents import expand_query
from app.rag import get_retriever

r = get_retriever()
qs = ["Do I need a bank account to receive my sales via Pix?",
      "preciso de conta bancária para receber vendas via Pix",
      "requisitos para habilitar o Pix na Getnet",
      "critérios de elegibilidade para habilitação do Pix domicílio bancário chave Pix"]
for q in qs:
    for qq in (q, expand_query(q)):
        hits = r.search(qq, k=15)
        ids = [getattr(h, 'doc', h).id if hasattr(h, 'doc') else h[0].id for h in hits]
        rank = ids.index('sup-pix-09') + 1 if 'sup-pix-09' in ids else None
        print(rank, '|', qq[:110], '|', ids[:5])
