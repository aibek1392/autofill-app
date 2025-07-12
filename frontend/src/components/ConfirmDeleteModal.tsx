import React from 'react'
import { motion } from "framer-motion"
import { Dialog } from "@headlessui/react"

interface ConfirmDeleteModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message?: string
  filename?: string
  loading?: boolean
}

export default function ConfirmDeleteModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Delete Document?",
  message = "Are you sure you want to delete this document? This action cannot be undone.",
  filename,
  loading 
}: ConfirmDeleteModalProps) {
  return (
    <Dialog open={isOpen} onClose={onClose} className="fixed z-50 inset-0 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" />
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        className="bg-white p-6 rounded-2xl shadow-xl z-10 w-full max-w-sm text-center"
      >
        <Dialog.Title className="text-xl font-bold mb-2">{title}</Dialog.Title>
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">{message}</p>
          {filename && (
            <p className="text-sm font-medium text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
              "{filename}"
            </p>
          )}
        </div>
        <div className="flex justify-center gap-4">
          <button 
            onClick={onClose} 
            className="px-4 py-2 rounded-md bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={onConfirm} 
            className={`px-4 py-2 rounded-md text-white transition-colors ${
              loading 
                ? 'bg-red-400 cursor-not-allowed' 
                : 'bg-red-500 hover:bg-red-600'
            }`}
            disabled={loading}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Deleting...
              </div>
            ) : (
              "Delete"
            )}
          </button>
        </div>
      </motion.div>
    </Dialog>
  )
} 