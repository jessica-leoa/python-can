#!/usr/bin/env python3
import can
import time
import sys

def ecu_simulador():
    print("="*60)
    print("🔧 ECU ROBUSTA PRO - SIMULADOR UDS COMPLETO")
    print("="*60)
    
    try:
        # Configura o barramento vcan0
        bus = can.interface.Bus('vcan0', interface='socketcan')
        print("✅ Status: Conectado ao barramento vcan0")
    except Exception as e:
        print(f"❌ Erro Crítico ao conectar: {e}")
        sys.exit(1)

    # Configurações de IDs UDS padrão
    rx_id = 0x7E0  # ID que a ECU escuta (vindo do Cliente)
    tx_id = 0x7E8  # ID que a ECU responde (indo para o Cliente)
    
    # Variáveis de Estado da ECU
    current_session = 0x01  # 0x01: Default, 0x02: Programming, 0x03: Extended
    security_unlocked = False
    count = 1

    print(f"📥 Escutando em: 0x{rx_id:X} | 📤 Respondendo em: 0x{tx_id:X}")
    print("-" * 60)
    print("🟢 ECU PRONTA - Aguardando sequência de mensagens...")
    print("-" * 60)

    try:
        while True:
            msg = bus.recv()
            if msg and msg.arbitration_id == rx_id:
                data = list(msg.data)
                # O SID (Service Identifier) é sempre o segundo byte no nosso esquema (PCI, SID, ...)
                sid = data[1] if len(data) > 1 else 0x00
                response = None
                status_desc = ""

                # --- Lógica de Serviços UDS (ISO 14229) ---

                # 1. Diagnostic Session Control (0x10)
                if sid == 0x10:
                    sub_function = data[2]
                    current_session = sub_function
                    # Resposta Positiva: [PCI, SID+0x40, SubFunction, Parâmetros...]
                    response = [0x06, 0x50, sub_function, 0x00, 0x32, 0x01, 0xF4]
                    status_desc = "Session Control OK"

                # 2. Security Access (0x27)
                elif sid == 0x27:
                    sub_function = data[2]
                    if sub_function == 0x01: # Request Seed
                        response = [0x04, 0x67, 0x01, 0xAB, 0xCD]
                        status_desc = "Security Access: Seed Enviada (0xABCD)"
                    elif sub_function == 0x02: # Send Key
                        key_recebida = data[3:5]
                        if key_recebida == [0xEF, 0xBE]: # Nossa chave "secreta"
                            security_unlocked = True
                            response = [0x02, 0x67, 0x02]
                            status_desc = "Security Access: Key Correta! ECU Desbloqueada"
                        else:
                            # Resposta Negativa (NRC 0x35 - Chave Inválida)
                            response = [0x03, 0x7F, 0x27, 0x35]
                            status_desc = "Security Access: Chave INCORRETA"

                # 3. Tester Present (0x3E)
                elif sid == 0x3E:
                    response = [0x01, 0x7E]
                    status_desc = "Tester Present OK"

                # 4. Request Download (0x34)
                elif sid == 0x34:
                    if security_unlocked:
                        response = [0x04, 0x74, 0x20, 0x04, 0x00]
                        status_desc = "Request Download OK"
                    else:
                        # NRC 0x33 - Segurança Necessária
                        response = [0x03, 0x7F, 0x34, 0x33]
                        status_desc = "Request Download NEGADO - ECU Bloqueada"

                # 5. Transfer Data (0x36)
                elif sid == 0x36:
                    block_seq = data[2]
                    response = [0x02, 0x76, block_seq]
                    status_desc = f"Transfer Data OK (Bloco {block_seq})"

                # 6. Request Transfer Exit (0x37)
                elif sid == 0x37:
                    response = [0x01, 0x77]
                    status_desc = "Transfer Exit OK"
                    security_unlocked = False # Tranca novamente para próxima sessão

                # Caso o serviço não seja reconhecido
                else:
                    response = [0x03, 0x7F, sid, 0x11] # NRC 0x11: Service Not Supported
                    status_desc = f"Serviço 0x{sid:02X} não suportado"

                # --- Impressão dos Logs no Terminal ---
                print(f"\n📥 [{count}] RX (0x{rx_id:X}): {' '.join(f'{b:02X}' for b in data)}")
                print(f"  → {status_desc}")

                if response:
                    # Preenchimento (Padding) com zeros até 8 bytes para o frame CAN
                    while len(response) < 8:
                        response.append(0x00)
                    
                    res_msg = can.Message(arbitration_id=tx_id, data=response, is_extended_id=False)
                    bus.send(res_msg)
                    print(f"📤 TX (0x{tx_id:X}): {' '.join(f'{b:02X}' for b in response)}")
                
                count += 1

    except KeyboardInterrupt:
        print("\n👋 Simulador ECU encerrado.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    ecu_simulador()