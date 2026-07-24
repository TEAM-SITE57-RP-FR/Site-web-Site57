/* =====================================================================
   SITE57_CORE.JS
   Moteur partagé entre Site57-Membre et Site57-Admin.
   Remplace window.storage (propre aux artefacts Claude) par des appels
   au contrôleur web2py "default" (kv_get / kv_set / kv_delete / kv_list).
   Chemins RELATIFS : fonctionne quel que soit le nom donné à
   l'application dans web2py.
   ===================================================================== */

window.storage = {
  async get(key){
    const res = await fetch('../default/kv_get?key='+encodeURIComponent(key));
    if(res.status===404) throw new Error('not_found');
    if(!res.ok) throw new Error('storage_error');
    return await res.json();
  },
  async set(key, value){
    const body = new URLSearchParams();
    body.set('key', key); body.set('value', value);
    const res = await fetch('../default/kv_set', {method:'POST', body});
    if(!res.ok) return null;
    return await res.json();
  },
  async delete(key){
    const body = new URLSearchParams();
    body.set('key', key);
    const res = await fetch('../default/kv_delete', {method:'POST', body});
    if(!res.ok) return null;
    return await res.json();
  },
  async list(prefix){
    const res = await fetch('../default/kv_list?prefix='+encodeURIComponent(prefix||''));
    if(!res.ok) return null;
    return await res.json();
  }
};

const K = {
  users:'site57:users', roles:'site57:roles', recruitment:'site57:recruitment',
  articles:'site57:articles', announcements:'site57:announcements', ideas:'site57:ideas',
  shop:'site57:shop', purchases:'site57:purchases', pages:'site57:pages', logs:'site57:logs',
  config:'site57:config'
};

let DB = { users:[], roles:[], recruitment:[], articles:[], announcements:[], ideas:[], shop:[], purchases:[], pages:{}, logs:[], config:null };

function uid(){ return Math.random().toString(36).slice(2,9); }
function now(){ return new Date().toLocaleString('fr-FR'); }
function esc(s){ return (s||'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function loadKey(key, fallback){
  try{
    const r = await window.storage.get(key);
    return r ? JSON.parse(r.value) : fallback;
  }catch(e){ return fallback; }
}
async function saveKey(key, value){
  try{ await window.storage.set(key, JSON.stringify(value)); }catch(e){ console.error('Erreur de sauvegarde', key, e); }
}

const DEFAULT_CONFIG = {
  siteName:'Site-57',
  tagline:'Terminal du personnel — accès restreint',
  links:[],
  banner:{active:false, text:''}
};

async function loadAll(){
  DB.users = await loadKey(K.users, null);
  DB.roles = await loadKey(K.roles, null);
  DB.recruitment = await loadKey(K.recruitment, []);
  DB.articles = await loadKey(K.articles, []);
  DB.announcements = await loadKey(K.announcements, []);
  DB.ideas = await loadKey(K.ideas, []);
  DB.shop = await loadKey(K.shop, []);
  DB.purchases = await loadKey(K.purchases, []);
  DB.pages = await loadKey(K.pages, {});
  DB.logs = await loadKey(K.logs, []);
  DB.config = await loadKey(K.config, null);

  if(!DB.roles){
    DB.roles = [
      {id:'developpeur', name:'Développeur', color:'#8a2b1f', perms:['all'], order:0, desc:'Accès total. Seul rôle habilité à créer et modifier les autres rôles.'},
      {id:'buildeur', name:'Bâtisseur', color:'#c98a2c', perms:['shop'], order:1, desc:'Construit et entretient les installations et la boutique du site.'},
      {id:'moderateur', name:'Modérateur', color:'#b23b2b', perms:['moderate'], order:2, desc:'Fait respecter le règlement intérieur : avertissements, exclusions, bannissements.'},
      {id:'animateur', name:'Animateur', color:'#3c5c3c', perms:['announcements','ideas'], order:3, desc:'Anime la vie du site : bulletins, événements, propositions.'},
      {id:'morpheur', name:'Morpheur', color:'#4a4a6a', perms:['articles'], order:4, desc:'Veille et rédaction : tient les journaux de recherche à jour.'},
      {id:'membre', name:'Membre', color:'#6b6b5f', perms:[], order:5, desc:'Personnel standard. Accès de lecture et fonctions de base.'}
    ];
    await saveKey(K.roles, DB.roles);
  }
  if(!DB.users){
    DB.users = [
      {username:'developeur1234', password:'developeur1234', role:'developpeur', credits:9999, status:'actif', warnings:[], joined: now()}
    ];
    await saveKey(K.users, DB.users);
  }
  if(DB.recruitment.length===0){
    DB.recruitment = [
      {id:uid(), roleTitle:'Bâtisseur', desc:'Recherche de personnel pour construire et entretenir les infrastructures du site.', status:'ouvert', createdBy:'developeur1234', applications:[]},
      {id:uid(), roleTitle:'Modérateur', desc:'Recherche de personnel pour faire respecter le règlement et gérer les incidents.', status:'ouvert', createdBy:'developeur1234', applications:[]},
      {id:uid(), roleTitle:'Animateur', desc:'Recherche de personnel pour animer la vie du site et organiser des événements.', status:'ouvert', createdBy:'developeur1234', applications:[]},
      {id:uid(), roleTitle:'Morpheur', desc:'Recherche de personnel pour la veille de nuit et la rédaction des journaux.', status:'ouvert', createdBy:'developeur1234', applications:[]}
    ];
    await saveKey(K.recruitment, DB.recruitment);
  }
  if(DB.shop.length===0){
    DB.shop = [
      {id:uid(), name:'Badge Vétéran', price:150, desc:'Un badge honorifique pour les membres de longue date.'},
      {id:uid(), name:'Accès Archives Niveau 2', price:300, desc:'Débloque la consultation des archives secondaires.'},
      {id:uid(), name:'Café du Site', price:20, desc:'Un café. Rien de plus, rien de moins.'}
    ];
    await saveKey(K.shop, DB.shop);
  }
  if(!DB.config){
    DB.config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
    await saveKey(K.config, DB.config);
  }
}

async function saveConfig(){ await saveKey(K.config, DB.config); }

function role(id){ return DB.roles.find(r=>r.id===id); }
function user(username){ return DB.users.find(u=>u.username===username); }
function hasPerm(sessionUser, perm){
  if(!sessionUser) return false;
  const r = role(sessionUser.role);
  if(!r) return false;
  return r.perms.includes('all') || r.perms.includes(perm);
}

/* Applique le nom / la devise / la bannière du site (config) au DOM */
function applyBranding(){
  const nameEls = document.querySelectorAll('[data-site-name]');
  const taglineEls = document.querySelectorAll('[data-site-tagline]');
  nameEls.forEach(el=>el.textContent = DB.config.siteName);
  taglineEls.forEach(el=>el.textContent = DB.config.tagline);
  document.title = document.title.replace('Site-57', DB.config.siteName);
  const bannerHost = document.getElementById('siteBanner');
  if(bannerHost){
    if(DB.config.banner && DB.config.banner.active && DB.config.banner.text){
      bannerHost.style.display='block';
      bannerHost.textContent = '⚠ ' + DB.config.banner.text;
    } else {
      bannerHost.style.display='none';
      bannerHost.textContent = '';
    }
  }
}
