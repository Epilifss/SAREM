type ErrorModalProps = {
  message: string | null
  onClose: () => void
}

export function ErrorModal({ message, onClose }: ErrorModalProps) {
  if (!message) return null

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="error-modal" role="alertdialog" aria-modal="true" aria-labelledby="error-modal-title" onMouseDown={event => event.stopPropagation()}>
        <div className="dashboard-panel-heading">
          <h2 id="error-modal-title">Não foi possível concluir</h2>
          <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">×</button>
        </div>
        <p>{message}</p>
        <div className="confirm-modal-actions">
          <button className="primary-action" type="button" onClick={onClose}>Entendi</button>
        </div>
      </section>
    </div>
  )
}