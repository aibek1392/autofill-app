import React, { useState, useEffect } from 'react'
import { Calendar, DollarSign, FileText, Loader2, AlertCircle } from 'lucide-react'

interface Transaction {
  id: string
  trans_date: string
  description: string
  amount: number
  line_number: number
  raw_text: string
  confidence: number
  external_transaction_id?: string
  created_at: string
}

interface TransactionsListProps {
  docId: string
  userId: string
  className?: string
}

const TransactionsList: React.FC<TransactionsListProps> = ({ docId, userId, className = '' }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTransactions = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'}/api/documents/${docId}/transactions`, {
        headers: {
          'X-User-ID': userId
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch transactions: ${response.statusText}`)
      }

      const result = await response.json()
      setTransactions(result.transactions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transactions')
      console.error('Failed to fetch transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (docId && userId) {
      fetchTransactions()
    }
  }, [docId, userId])

  const formatAmount = (amount: number) => {
    const isNegative = amount < 0
    const absAmount = Math.abs(amount)
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(absAmount)
    
    return (
      <span className={isNegative ? 'text-red-600' : 'text-green-600'}>
        {isNegative ? '-' : '+'}{formatted}
      </span>
    )
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800'
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span className="text-gray-600">Loading transactions...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-6 bg-red-50 border border-red-200 rounded-lg ${className}`}>
        <div className="flex items-center text-red-800">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span className="font-medium">Error loading transactions</span>
        </div>
        <p className="text-red-600 text-sm mt-1">{error}</p>
        <button 
          onClick={fetchTransactions}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (transactions.length === 0) {
    return (
      <div className={`p-6 text-center text-gray-500 ${className}`}>
        <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p className="text-lg font-medium">No transactions found</p>
        <p className="text-sm">This document may not contain financial statement data or transactions couldn't be parsed.</p>
      </div>
    )
  }

  const totalTransactions = transactions.length
  const totalAmount = transactions.reduce((sum, t) => sum + (t.amount || 0), 0)
  const avgConfidence = transactions.reduce((sum, t) => sum + (t.confidence || 0), 0) / transactions.length

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">{totalTransactions}</div>
          <div className="text-sm text-blue-800">Total Transactions</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border">
          <div className="text-2xl font-bold text-green-600">
            {formatAmount(totalAmount)}
          </div>
          <div className="text-sm text-green-800">Net Amount</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border">
          <div className="text-2xl font-bold text-purple-600">{(avgConfidence * 100).toFixed(1)}%</div>
          <div className="text-sm text-purple-800">Avg Confidence</div>
        </div>
      </div>

      {/* Transactions List */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <DollarSign className="w-5 h-5 mr-2 text-green-600" />
            Parsed Transactions
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Automatically extracted from financial statement PDF
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Line #
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((transaction, index) => (
                <tr key={transaction.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                      {transaction.trans_date ? formatDate(transaction.trans_date) : 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={transaction.description}>
                      {transaction.description || 'No description'}
                    </div>
                    {transaction.external_transaction_id && (
                      <div className="text-xs text-gray-500 mt-1">
                        ID: {transaction.external_transaction_id}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-right">
                    {transaction.amount !== null ? formatAmount(transaction.amount) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getConfidenceColor(transaction.confidence || 0)}`}>
                      {((transaction.confidence || 0) * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                    {transaction.line_number || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw Text Details (Expandable) */}
      <details className="bg-gray-50 border border-gray-200 rounded-lg">
        <summary className="px-6 py-4 cursor-pointer font-medium text-gray-900 hover:bg-gray-100">
          View Raw Transaction Data ({transactions.length} entries)
        </summary>
        <div className="px-6 py-4 border-t border-gray-200 space-y-3">
          {transactions.map((transaction, index) => (
            <div key={transaction.id} className="bg-white p-3 rounded border text-sm">
              <div className="font-medium text-gray-900 mb-1">
                Line {transaction.line_number} - {transaction.trans_date ? formatDate(transaction.trans_date) : 'No Date'}
              </div>
              <div className="font-mono text-xs text-gray-600 bg-gray-100 p-2 rounded">
                {transaction.raw_text || 'No raw text available'}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}

export default TransactionsList

