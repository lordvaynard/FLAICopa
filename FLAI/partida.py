import streamlit as st
import pandas as pd
import numpy as np
import random
from scipy.stats import poisson

selecoes = pd.read_excel('FLAI/DadosCopaDoMundoQatar2022.xlsx', sheet_name = 'selecoes', index_col = 0)
jogos = pd.read_excel('FLAI/DadosCopaDoMundoQatar2022.xlsx', sheet_name = 'jogos')

jogos.head()

selecoes.head()

fifa = selecoes['PontosRankingFIFA']
a, b = min(fifa), max(fifa) #capturando os limites
fa, fb = 0.15, 1 #calculo da transformação linear de escala numérica
b1 = (fb-fa)/(b-a) #transformação linear max-min dividido por maximo do ranking - min do ranking
b0 = fb - b*b1 #transformação linear
forca = b0 +b1*fifa
#forca

def MediasPoisson(selecao1, selecao2):
  forca1 = forca[selecao1]
  forca2 = forca[selecao2]
  mgols = 2.75
  l1 = mgols*forca1/(forca1 + forca2)
  l2 = mgols - l1
  return [l1, l2]

def Resultado(gols1, gols2):
  if gols1 > gols2:
    resultado = 'V'
  elif gols2 > gols1:
    resultado = 'D'
  else:
    resultado = 'E'
  return resultado

def Pontos(gols1, gols2):
  resultado = Resultado(gols1, gols2)
  if resultado == 'V':
    pontos1, pontos2 = 3,0
  elif resultado == 'E':
    pontos1, pontos2 = 1,1
  elif resultado == 'D':
    pontos1, pontos2 = 0,3
  return [pontos1, pontos2, resultado]

def Jogo(selecao1, selecao2):
  l1,  l2 = MediasPoisson(selecao1, selecao2)
  gols1 = int(np.random.poisson(lam = l1, size = 1))
  gols2 = int(np.random.poisson(lam = l2, size = 1))
  saldo1 = gols1 - gols2
  saldo2 = -saldo1
  pontos1, pontos2, resultado = Pontos(gols1, gols2)
  placar = '{}x{}'.format(gols1, gols2)
  return [gols1, gols2, saldo1, saldo2, pontos1, pontos2, resultado, placar]

def Distribuicao(media):
  probs = []
  for i in range(4): #probabilidade até 4 gols (goleada)
    probs.append(poisson.pmf(i,media))
  probs.append(1 - sum(probs))#placares restantes acima de 4 gols
  return pd.Series(probs, index = ['0', '1', '2', '3', '4+'])

def ProbabilidadesPartida(selecao1, selecao2):
  l1, l2 = MediasPoisson(selecao1, selecao2)
  d1, d2 = Distribuicao(l1), Distribuicao(l2)
  matriz = np.outer(d1, d2)
  vitoria = np.tril(matriz).sum() -  np.trace(matriz) #considera somente a matriz inferior (lower)
  empate = np.trace(matriz) #considera somente a diagonal da matriz
  derrota = np.triu(matriz).sum() - np.trace(matriz) #considera somente a matriz superior (upper)

  probs = np.around([vitoria, empate, derrota], 3) #arredondamento
  probsp = [f'{100*i:.1f}%' for i in probs ]

  nomes = ['0', '1', '2', '3', '4+']
  matriz = pd.DataFrame(matriz, columns = nomes, index = nomes)
  matriz.index = pd.MultiIndex.from_product([[selecao1], matriz.index])
  matriz.columns = pd.MultiIndex.from_product([[selecao2], matriz.columns])

  output = {'selecao1': selecao1, 'selecao2': selecao2,
            'f1': forca[selecao1], 'f2': forca[selecao2],
            'media1': l1, 'media2': l2,
            'probabilidades': probsp, 'matriz': matriz}

  return output

ProbabilidadesPartida('Brasil', 'França')

jogos['Vitória'] = None
jogos['Empate'] = None
jogos['Derrota'] = None

for i in range(jogos.shape[0]):
  selecao1 = jogos['seleção1'][i]
  selecao2 = jogos['seleção2'][i]
  v, e, d = ProbabilidadesPartida(selecao1, selecao2)['probabilidades']
  jogos.at[i, 'Vitória'] = v
  jogos.at[i, 'Empate'] = e
  jogos.at[i, 'Derrota'] = d

jogos.to_excel('FLAI/outputEstimativasJogosCopa.xlsx')
#jogos

#d1, d2 = np.around(Distribuicao(1.478048191315901),2), np.around(Distribuicao(1.271951808684099),2)
#pd.DataFrame(np.outer(d1,d2)*100)
  
#app Começa agora
listaselecoes1 = selecoes.index.tolist()
listaselecoes1.sort()
listaselecoes2 = listaselecoes1.copy()

j1, j2 = st.columns(2)
selecao1 = j1.selectbox('Escolha a primeira Seleção', listaselecoes1)
listaselecoes2.remove(selecao1)
selecao2 = j2.selectbox('Escolha a primeira Seleção', listaselecoes2)
st.markdown('---')

jogo = ProbabilidadesPartida(selecao1, selecao2)
prob = jogo['probabilidades']
matriz = jogo['matriz']

col1, col2, col3, col4, col5 = st.columns(5)
col1.image(selecoes.loc[selecao1, 'LinkBandeiraGrande'])
col2.metric(selecao1, prob[0])
col3.metric('Empate', prob[1])
col4.metric(selecao2, prob[2])
col5.image(selecoes.loc[selecao2, 'LinkBandeiraGrande'])

st.markdown('---')
st.markdown("## Probabilidades dos Placares")

def aux(x):
    return f'{str(round(100*x,1))}%'

st.table(matriz.applymap(aux))

st.markdown('---')
st.markdown('## Probabilidades dos Jogos da Copa')

jogoscopa = pd.read_excel('outputEstimativasJogosCopa.xlsx', index_col = 0)
st.table(jogoscopa[['grupo', 'seleção1', 'seleção2', 'Vitória', 'Empate', 'Derrota']])