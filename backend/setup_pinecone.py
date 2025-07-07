#!/usr/bin/env python3
"""
Pinecone Setup Script for AI Autofill Form App
This script helps you create the Pinecone index and get the correct configuration.
"""

import os
import sys
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_pinecone():
    """Set up Pinecone index for the autofill app"""
    
    # Get API key from environment or user input
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("🔑 Pinecone API Key not found in environment.")
        api_key = input("Please enter your Pinecone API Key: ").strip()
        if not api_key:
            print("❌ API key is required. Get it from: https://app.pinecone.io/")
            return False
    
    try:
        # Initialize Pinecone client
        print("🔗 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        # Configuration
        index_name = "autofill-documents"
        dimension = 1536  # OpenAI embedding dimension
        metric = "cosine"
        
        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if index_name in index_names:
            print(f"✅ Index '{index_name}' already exists!")
        else:
            print(f"📝 Creating index '{index_name}'...")
            
            # Create index with serverless spec (modern Pinecone)
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"✅ Index '{index_name}' created successfully!")
        
        # Get index info
        index_info = pc.describe_index(index_name)
        print(f"\n📊 Index Information:")
        print(f"   Name: {index_info.name}")
        print(f"   Dimension: {index_info.dimension}")
        print(f"   Metric: {index_info.metric}")
        print(f"   Host: {index_info.host}")
        
        # Test connection
        print("\n🧪 Testing connection...")
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        print(f"✅ Connection successful! Vector count: {stats.total_vector_count}")
        
        # Generate environment variables
        print("\n" + "="*60)
        print("🎯 CONFIGURATION FOR YOUR .env FILE:")
        print("="*60)
        print(f"PINECONE_API_KEY={api_key}")
        print(f"PINECONE_INDEX_NAME={index_name}")
        print("# Note: PINECONE_ENVIRONMENT is not needed in modern Pinecone")
        print("="*60)
        
        # Write to .env file if it exists
        env_file = ".env"
        if os.path.exists(env_file):
            print(f"\n📝 Updating {env_file}...")
            update_env_file(env_file, api_key, index_name)
        else:
            print(f"\n📝 Creating {env_file}...")
            create_env_file(env_file, api_key, index_name)
            
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Pinecone: {str(e)}")
        print("\n💡 Common issues:")
        print("   1. Invalid API key")
        print("   2. Network connectivity")
        print("   3. Quota limits reached")
        print("\n🔗 Get help at: https://docs.pinecone.io/")
        return False

def update_env_file(env_file, api_key, index_name):
    """Update existing .env file with Pinecone configuration"""
    try:
        # Read existing content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add Pinecone variables
        updated_lines = []
        pinecone_vars = {
            'PINECONE_API_KEY': api_key,
            'PINECONE_INDEX_NAME': index_name
        }
        
        # Track which variables we've updated
        updated_vars = set()
        
        for line in lines:
            if line.strip().startswith('PINECONE_API_KEY='):
                updated_lines.append(f"PINECONE_API_KEY={api_key}\n")
                updated_vars.add('PINECONE_API_KEY')
            elif line.strip().startswith('PINECONE_INDEX_NAME='):
                updated_lines.append(f"PINECONE_INDEX_NAME={index_name}\n")
                updated_vars.add('PINECONE_INDEX_NAME')
            elif line.strip().startswith('PINECONE_ENVIRONMENT='):
                # Remove old PINECONE_ENVIRONMENT variable
                updated_lines.append("# PINECONE_ENVIRONMENT is no longer needed\n")
            else:
                updated_lines.append(line)
        
        # Add any missing variables
        for var, value in pinecone_vars.items():
            if var not in updated_vars:
                updated_lines.append(f"{var}={value}\n")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated {env_file} with Pinecone configuration")
        
    except Exception as e:
        print(f"⚠️  Could not update {env_file}: {str(e)}")
        print("Please update it manually with the configuration shown above.")

def create_env_file(env_file, api_key, index_name):
    """Create new .env file with basic configuration"""
    try:
        env_content = f"""# Backend Environment Variables for AI Autofill Form App

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key

# Pinecone Configuration
PINECONE_API_KEY={api_key}
PINECONE_INDEX_NAME={index_name}

# Supabase Configuration (Required)
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# App Configuration
DEBUG=true
CORS_ORIGINS=http://localhost:3000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# LangSmith Configuration (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=autofill-form-app
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_file} with Pinecone configuration")
        print("⚠️  Don't forget to add your OpenAI and Supabase credentials!")
        
    except Exception as e:
        print(f"⚠️  Could not create {env_file}: {str(e)}")

def main():
    print("🚀 Pinecone Setup for AI Autofill Form App")
    print("=" * 50)
    
    if setup_pinecone():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Add your OpenAI API key to .env file")
        print("   2. Add your Supabase credentials to .env file")
        print("   3. Restart your backend server")
        print("   4. Test document upload functionality")
    else:
        print("\n❌ Setup failed. Please check your API key and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 