#!/usr/bin/env python3
import can
import time
import sys
import subprocess
from datetime import datetime

class ClienteOTASuper:
    def __init__(self, channel='vcan0'):
        print("="*70)
        print("🚀 CLIENTE OTA UDS - SISTEMA DE ATUALIZAÇÃO PROFISSIONAL")
        print("="*70)
        try:
            self.bus = can.interface.Bus(channel, interface='socketcan')
            self.tx_id = 0x7E0
            self.rx_id = 0x7E8
            print(f"✅ Conectado ao vcan0 | TX: 0x{self.tx_id:X} | RX: 0x{self.rx_id:X}")
        except Exception as e:
            print(f"❌ Erro ao inicializar barramento: {e}")
            sys.exit(1)

    def log_transacao(self, direcao, id_can, dados, desc=""):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        seta = "📤 TX" if direcao == "out" else "📥 RX"
        print(f"[{timestamp}] {seta} (0x{id_can:X}): {' '.join(f'{b:02X}' for b in dados)}  [{desc}]")

    def requisitar_uds(self, payload, descricao):
        # Garante 8 bytes
        while len(payload) < 8:
            payload.append(0x00)
        
        # Envia
        self.log_transacao("out", self.tx_id, payload, descricao)
        msg = can.Message(arbitration_id=self.tx_id, data=payload, is_extended_id=False)
        self.bus.send(msg)

        # Recebe
        start_time = time.time()
        while (time.time() - start_time) < 1.5: # Timeout de 1.5s
            resposta = self.bus.recv(timeout=0.1)
            if resposta and resposta.arbitration_id == self.rx_id:
                # Verifica se é Resposta Positiva (SID enviado + 0x40)
                if resposta.data[1] == (payload[1] + 0x40):
                    self.log_transacao("in", self.rx_id, resposta.data, "Resposta POSITIVA")
                    return True, resposta.data
                # Verifica se é Resposta Negativa (0x7F)
                elif resposta.data[1] == 0x7F:
                    self.log_transacao("in", self.rx_id, resposta.data, f"ERRO UDS: NRC 0x{resposta.data[3]:02X}")
                    return False, resposta.data
        
        print(f"⚠️  Timeout: ECU não respondeu ao comando {descricao}")
        return False, None

    def executar_fluxo_ota(self):
        print("\n" + "-"*70)
        print("🚀 INICIANDO SEQUÊNCIA DE ATUALIZAÇÃO")
        print("-"*70)

        # PASSO 1: Diagnostic Session Control (0x10) - Modo Programação
        success, _ = self.requisitar_uds([0x02, 0x10, 0x02], "Session Control: Programming")
        if not success: return
        time.sleep(0.5)

        # PASSO 2: Security Access (0x27) - Seed & Key
        print("\n🔑 Solicitando Acesso de Segurança...")
        success, res_seed = self.requisitar_uds([0x02, 0x27, 0x01], "Security Access: Request Seed")
        if not success: return
        
        # Simulação de algoritmo de chave: Enviamos 0xEFBE
        time.sleep(0.5)
        success, _ = self.requisitar_uds([0x04, 0x27, 0x02, 0xEF, 0xBE], "Security Access: Send Key")
        if not success: return
        time.sleep(0.5)

        # PASSO 3: Request Download (0x34)
        print("\n📦 Solicitando Permissão de Download...")
        success, _ = self.requisitar_uds([0x06, 0x34, 0x00, 0x12, 0x34, 0x00, 0x04, 0x00], "Request Download (Addr=0x1234, Size=4)")
        if not success: return
        time.sleep(0.5)

        # PASSO 4: Transfer Data (0x36)
        print("\n💾 Transferindo Blocos de Dados...")
        success, _ = self.requisitar_uds([0x05, 0x36, 0x01, 0xDE, 0xAD, 0xBE, 0xEF], "Transfer Data: Bloco 1")
        if not success: return
        time.sleep(0.5)

        # PASSO 5: Request Transfer Exit (0x37)
        print("\n🏁 Finalizando Transferência...")
        success, _ = self.requisitar_uds([0x01, 0x37], "Request Transfer Exit")
        if not success: return

        print("\n" + "="*70)
        print("✨ SISTEMA ATUALIZADO COM SUCESSO!")
        print("="*70)

    def encerrar(self):
        self.bus.shutdown()
        print("\n🔌 Barramento CAN finalizado.")

def configurar_interface():
    print("🔧 Verificando interface vcan0...")
    subprocess.run(['sudo', 'modprobe', 'vcan'], check=True)
    subprocess.run(['sudo', 'ip', 'link', 'set', 'up', 'vcan0'], stderr=subprocess.DEVNULL)

def main():
    configurar_interface()
    input("\n⏎  Pressione ENTER para iniciar o cliente UDS...")
    
    cliente = ClienteOTASuper()
    try:
        cliente.executar_fluxo_ota()
    finally:
        cliente.encerrar()

if __name__ == "__main__":
    main()