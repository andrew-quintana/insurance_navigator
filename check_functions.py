import asyncpg
import asyncio

async def check_functions():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/insurance_navigator')
    
    # Check which functions exist and their security settings
    result = await conn.fetch('''
        SELECT 
            proname as function_name,
            prosecdef as security_definer,
            CASE WHEN prosecdef THEN 'SECURITY DEFINER' ELSE 'SECURITY INVOKER' END as security_type
        FROM pg_proc 
        WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        AND proname IN ('is_admin', 'is_admin_user', 'get_current_user_id')
        ORDER BY proname;
    ''')
    
    print('Current Function Security Status:')
    print('=' * 50)
    for row in result:
        print(f'{row["function_name"]}: {row["security_type"]}')
    
    # Check function definitions
    for func in ['is_admin', 'is_admin_user', 'get_current_user_id']:
        try:
            definition = await conn.fetchval('''
                SELECT pg_get_functiondef(oid) 
                FROM pg_proc 
                WHERE proname = $1 
                AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            ''', func)
            
            if definition:
                print(f'\n{func.upper()} FUNCTION:')
                print('-' * 30)
                print(definition[:300] + '...' if len(definition) > 300 else definition)
            else:
                print(f'\n{func.upper()} FUNCTION: NOT FOUND')
        except Exception as e:
            print(f'Error checking {func}: {e}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_functions()) 