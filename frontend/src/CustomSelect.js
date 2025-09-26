import React, { useState } from 'react';
import { FaChevronDown } from 'react-icons/fa';
import './UserProfile.css'; 

const CustomSelect = ({ value, onChange, options, placeholder, name }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="custom-select-container">
            <div
                className="custom-select-header"
                onClick={() => setIsOpen(!isOpen)}
            >
                {value ? `Quarter ${value}` : placeholder}
                <FaChevronDown className={`chevron ${isOpen ? 'open' : ''}`} />
            </div>
            {isOpen && (
                <div className="custom-select-options">
                    {options.map(option => (
                        <div
                            key={option.value}
                            className="custom-select-option"
                            onClick={() => {
                                onChange({ target: { name, value: option.value } });
                                setIsOpen(false);
                            }}
                        >
                            {option.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CustomSelect;
