import threading
import time
import datetime
from plyer import notification
from back.database import create_connection, create_connection_Protheus

# Módulos
from front.windows.corporativo_view import CorporativoModule
from front.windows.varejo_view import VarejoModule
from front.windows.exportacao_view import ExportacaoModule

monitorar_bo_event = threading.Event()

def monitorar_bo_embarcadas():
    def tarefa():
        while not monitorar_bo_event.is_set():
            try:
                horario = datetime.datetime.now()
                hora = (f"as {horario.hour}:{horario.minute}")

                print("Monitorando BOs embarcadas " + hora)
                conn = create_connection()
                conn_Protheus = create_connection_Protheus()
                if conn is None or conn_Protheus is None:
                    print("Erro de conexão com o banco.")
                    time.sleep(60)
                    continue

                cursor = conn.cursor()
                cursor.execute("SELECT bo_number, op FROM bo_records WHERE status <> 'Embarcado' AND D_E_L_E_T_ <> '*'")
                bos = cursor.fetchall()

                for bo_number, op in bos:
                    cursor_mik = conn_Protheus.cursor()
                    
                    cursor_mik.execute("""
                        SELECT COUNT(*) FROM SC6010
                        WHERE C6_NUM = ?
                        AND D_E_L_E_T_ <> '*'
                        AND (C6_BLQ = 'R' OR C6_BLQ = '')
                    """, str(op))
                    result = cursor_mik.fetchone()
                    total_itens = result[0] if result is not None else 0

                    cursor_mik.execute("""
                        SELECT COUNT(*) FROM SC6010
                        WHERE C6_NUM = ?
                        AND D_E_L_E_T_ <> '*'
                        AND (
                            C6_BLQ = 'R'
                            OR (C6_BLQ = '' AND C6_NOTA <> '')
                        )
                    """, str(op))
                    result = cursor_mik.fetchone()
                    itens_prontos = result[0] if result is not None else 0
                    
                    cursor_mik.close()

                    if total_itens > 0 and itens_prontos == total_itens:
                        cursor.execute("UPDATE bo_records SET status = 'Embarcado' WHERE bo_number = ?", (bo_number,))
                        conn.commit()
                        
                        notification.notify(
                            title='Alerta de Embarque',
                            message=f'BO {bo_number} saiu para embarque',
                            app_name='SAREM',
                            timeout=10
                        )

                        print(f"BO {bo_number} marcada como Embarcada.")

                        # Se precisar atualizar as interfaces, faça a importação condicional aqui
                        try:
                            if hasattr(CorporativoModule, "instance") and CorporativoModule.instance is not None:
                                CorporativoModule.instance.carregar_bos()
                        except Exception:
                            pass
                        try:
                            if hasattr(VarejoModule, "instance") and VarejoModule.instance is not None:
                                VarejoModule.instance.carregar_bos()
                        except Exception:
                            pass
                        try:
                            if hasattr(ExportacaoModule, "instance") and ExportacaoModule.instance is not None:
                                ExportacaoModule.instance.carregar_bos()
                        except Exception:
                            pass

                cursor.close()
                conn.close()
                conn_Protheus.close()
            except Exception as e:
                print(f"Erro ao monitorar BOs embarcadas: {e}")
            if monitorar_bo_event.wait(60):
                print("Monitoramento de BOs embarcadas interrompido.")
                break

    monitorar_bo_event.clear()
    threading.Thread(target=tarefa, daemon=True).start()
