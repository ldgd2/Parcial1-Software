export async function generateDeterministicHash(data: any): Promise<string> {
    const jsonStr = deterministicStringify(data);
    if (crypto.subtle) {
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(jsonStr);
      const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
      
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } else {
      // Pseudo-hash fallback para http sin localhost
      let hash = 0;
      for (let i = 0; i < jsonStr.length; i++) {
        const char = jsonStr.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }
      return Math.abs(hash).toString(16).padStart(8, '0');
    }
}

function deterministicStringify(obj: any): string {
    if (obj === null || typeof obj !== 'object') {
        return JSON.stringify(obj);
    }

    if (Array.isArray(obj)) {
        const items = obj.map(item => item === undefined ? 'null' : deterministicStringify(item));
        return '[' + items.join(',') + ']';
    }

    const sortedKeys = Object.keys(obj).sort();
    const pairs: string[] = [];
    
    for (const key of sortedKeys) {
        const value = obj[key];
        // En JSON estándar, propiedades undefined se omiten
        if (value !== undefined) {
            pairs.push(JSON.stringify(key) + ':' + deterministicStringify(value));
        }
    }
    
    return '{' + pairs.join(',') + '}';
}
