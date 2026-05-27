from datetime import datetime
import os

gastos = []
agora = datetime.now()

def calculomes(renda, gastos):
    total = sum(valor for data, valor in gastos)
    print("O total gasto esse mês foi de R$", total)

    final = renda - total

    if final > 0:
        print("Sobrou: R$", final)
    elif final < 0:
        print("Você está devendo: R$", final)
    else:
        print(f"Não te sobrou nada [R${final}]")

    print("Salvando no seu arquivo...")

    with open("gastos.txt", "a", encoding="utf-8") as arquivo:
        arquivo.write(f"\nRenda mensal: R${renda:.2f}\n\n")
        for data, valor in gastos:
            linha = f"{data.strftime('%d/%m/%Y %H:%M')} - Gasto: R${valor:.2f}\n"
            arquivo.write(linha)

    print("Arquivo salvo com sucesso!")

while True:             
    # Menu
    print("1- cadastrar gasto hoje")
    print("2- cadastrar renda")
    print("3- calcular gastos")
    print("4- escolher dia(anterior ou futuro)")
    print("0- sair")

    opcao = int(input("--"))

    match opcao:
        case 0:
            os.system('cls')
            print("finalizado")
            break

        case 1:
            for x in range(1):
                print(f"\n Data: {agora.strftime('%d/%m/%Y %H:%M')}")
                valores = float(input("Digite os valores gastos esse dia: R$ ").replace(",", "."))
                gastos.append((datetime.now(), valores))

        case 2:
                renda = float(input("Digite sua renda mensal: R$ ").replace(",", "."))

        case 3:
                calculomes(renda, gastos)

        case 4:
            print(f"\n Data: {agora.strftime('%d/%m/%Y %H:%M')}")
            