import { useEffect, useRef, useState } from 'react'

type SearchSelectModalProps = {
  label: string
  value: string
  placeholder: string
  options: string[]
  onChange: (value: string) => void
}

export function SearchSelectModal({ label, value, placeholder, options, onChange }: SearchSelectModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setIsOpen(false)
    }

    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [])

  const filteredOptions = options
    .filter(option => option.toLocaleLowerCase().includes(value.toLocaleLowerCase()))
    .slice(0, 8)

  return (
    <div className="search-select" ref={containerRef}>
      <label>{label}</label>
      <input
        type="text"
        value={value}
        onFocus={() => setIsOpen(true)}
        onChange={event => {
          onChange(event.target.value)
          setIsOpen(true)
        }}
        placeholder={placeholder}
        role="combobox"
        aria-expanded={isOpen}
        aria-autocomplete="list"
        autoComplete="off"
      />

      {isOpen && (
        <div className="search-select-options" role="listbox">
          {filteredOptions.length === 0 ? (
            <p className="search-select-empty">Nenhuma sugestão encontrada.</p>
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
      )}
    </div>
  )
}