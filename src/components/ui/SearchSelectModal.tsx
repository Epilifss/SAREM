import { useEffect, useState } from 'react'

type SearchSelectModalProps = {
  label: string
  value: string
  placeholder: string
  options: string[]
  onChange: (value: string) => void
}

export function SearchSelectModal({ label, value, placeholder, options, onChange }: SearchSelectModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!isOpen) setSearch('')
  }, [isOpen])

  const filteredOptions = options.filter(option => option.toLocaleLowerCase().includes(search.toLocaleLowerCase()))

  return (
    <div className="search-select">
      <label>{label}</label>
      <button type="button" className="search-select-trigger" onClick={() => setIsOpen(true)}>
        <span className={value ? '' : 'search-select-placeholder'}>{value || placeholder}</span>
        <span aria-hidden="true">⌄</span>
      </button>

      {isOpen && (
        <div className="search-select-backdrop" role="presentation" onMouseDown={() => setIsOpen(false)}>
          <div className="search-select-modal" role="dialog" aria-modal="true" aria-label={label} onMouseDown={event => event.stopPropagation()}>
            <div className="search-select-modal-header">
              <h3>{label}</h3>
              <button type="button" className="search-select-close" onClick={() => setIsOpen(false)} aria-label="Fechar">×</button>
            </div>
            <input
              autoFocus
              type="search"
              value={search}
              onChange={event => setSearch(event.target.value)}
              placeholder={`Pesquisar ${label.toLocaleLowerCase()}`}
            />
            <div className="search-select-options">
              {filteredOptions.length === 0 ? (
                <p className="search-select-empty">Nenhuma opção encontrada.</p>
              ) : filteredOptions.map(option => (
                <button
                  type="button"
                  className={`search-select-option${option === value ? ' selected' : ''}`}
                  key={option}
                  onClick={() => {
                    onChange(option)
                    setIsOpen(false)
                  }}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}