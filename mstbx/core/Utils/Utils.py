# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# Utils     : Este módulo contem multiples classes que podem ajudar                           #
#             com tarefas generais.                                                           #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 12 de Junho do 2024.                                               #
# $rev$     : Não testado ainda.                                                              #                    #
# Mudanças no código:                                                                         #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
#// ****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
#// ****************************************************************************************//#

import os
import sys
import warnings
import time 
#import Utils 
from datetime import datetime
from colorama import Fore 
warnings.filterwarnings("ignore")


#// ****************************************************************************************//#
# Definição da classe  UnixMessage                                                          #
#// ****************************************************************************************//#

class UnixMessage:
    def __init__(self) -> None:
        pass 

    def makedir(self, dirs: list):
        ''' Nesta método cria um conjunto de pastas que via permitir
            organizar a simulação.
        '''
        for j in dirs: 
            if not os.path.exists(j):
                os.mkdir(j)
                UnixMessage().message(message=f"Making the folder: {j}", type="info")
    
    def message(self, message: str, type: str):
        ''' Este método permite imprimir no terminal determinados 
            mensagens que o usuario quer enviar. 
        '''
        if type == "info":
            print(Fore.GREEN +   f"[INFO     ] {message}." + Fore.RESET)
        elif type == "warning": 
            print(Fore.YELLOW +  f"[WARNING  ] {message}." + Fore.RESET)
        elif type == "error":
            print(Fore.RED +     f"[ERROR    ] {message}." + Fore.RESET)
        else: 
            print("[ERROR     ] You don't have to select any option.")

    def date(self):
        ''' Este método permite obter a data actual para 
            adicionar nos archivos ou logs
        '''
        now = datetime.now()
        formatted_time = now.strftime("%m/%d/%Y %H:%M:%S.%f")
        return formatted_time
