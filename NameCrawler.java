package wikinames;

/** 
 * This class uses the wikipedia API to gather a list of English person names
 * by querying the categories like "1955 deaths", and gathering all of their 
 * members.
 * 
 * @author ccb
 *
 */

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;

import org.w3c.dom.*;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.ParserConfigurationException;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException; 

public class NameCrawler {

	DocumentBuilder docBuilder;
	
	public NameCrawler() throws SAXParseException, SAXException, ParserConfigurationException {
    	DocumentBuilderFactory docBuilderFactory = DocumentBuilderFactory.newInstance();
    	docBuilder = docBuilderFactory.newDocumentBuilder();

	}

	/**
	 * Queries wikipedia for all people who were born or died in the
	 * specified year. 
	 * @param year
	 */
	public ArrayList<String> getEnglishNamesForYear(int year) throws IOException, SAXException {
		ArrayList<String> nameList = new ArrayList<String>(); 
		String[] humanLifeEvents = {"births", "deaths"};
		for(String birthDeath : humanLifeEvents) {
			Document doc = docBuilder.parse("https://en.wikipedia.org/w/api.php?action=query&format=xml&continue&list=categorymembers&cmlimit=500&cmtitle=Category:" + year + "%20" + birthDeath);
			//api.query.categrymembers
			// NodeList people = doc.getDocumentElement().getChildNodes().item(1).getFirstChild().getChildNodes();
			NodeList people = doc.getElementsByTagName("cm");
	    	for(int i = 0; i < people.getLength(); i++) {
	    		Node person = people.item(i);
	    		String name = null;
	    		try{
	    			name = person.getAttributes().getNamedItem("title").getNodeValue();
	    		} catch (Exception e) {
	    			e.printStackTrace();
	    		}
	    		nameList.add(name);
	    	}
	    	
	    	Node queryContinues = doc.getElementsByTagName("continue").item(0);
	    	while(queryContinues != null && queryContinues.getNodeName().equals("continue")) {
	    		String contName = queryContinues.getAttributes().getNamedItem("cmcontinue").getNodeValue();
	    		contName = contName.replaceAll("\\s", "%20");
	    		
	    		doc = docBuilder.parse("https://en.wikipedia.org/w/api.php?action=query&format=xml&continue&list=categorymembers&cmlimit=500&cmtitle=Category:" + year + "%20" + birthDeath + "&cmcontinue=" + contName);
	    		// people = doc.getDocumentElement().getChildNodes().item(1).getFirstChild().getChildNodes();
	    		people = doc.getElementsByTagName("cm");
	    	   	for(int i = 0; i < people.getLength(); i++) {
	    	    	Node person = people.item(i);
	    	   		String name = person.getAttributes().getNamedItem("title").getNodeValue();
	    	   		nameList.add(name);
	    	   	}
	    	   	queryContinues = doc.getElementsByTagName("continue").item(0);
	    	}
		}
    	return nameList;
	}
	
	/** 
	 * Creates a HashMap that maps from langCode --> name for
	 * all languages that have inter-language links from the English 
	 * page about the person.  If no inter-language links exist
	 * then the method returns a Map with one pair (the lang code "en",
	 * and the name).
	 *  
	 * @param name a person's name in English
	 * @return a Map from langCode onto foreign transliteration
	 * @throws IOException
	 * @throws SAXException
	 */
	public HashMap<String, String> getTransliterations(String name) throws IOException, SAXException {
		HashMap<String, String> transliterations = new HashMap<String, String>();
		String urlName = name.replaceAll("\\s", "%20");
		Document doc = null;
		boolean retry = true;
		while(retry){
			try {
				doc = docBuilder.parse("https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=langlinks&lllimit=300&titles=" + urlName);
				retry = false;
			} catch (IOException e) {
				retry = true;
			}	
		}
		
    	// Document doc = docBuilder.parse("https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=langlinks&lllimit=300&titles=" + urlName);
    	Node page = doc.getDocumentElement().getFirstChild().getFirstChild().getFirstChild();
    	// if there are inter-language links for this page...
		if(page.getFirstChild() != null) {
			NodeList languageLinks = page.getFirstChild().getChildNodes();
	    	for(int i = 0; i < languageLinks.getLength(); i++) {
	    		Node languageLink = languageLinks.item(i);
	    		String langCode = languageLink.getAttributes().getNamedItem("lang").getNodeValue();
	    		try {
	    			String nameInThatLang = languageLink.getFirstChild().getNodeValue();
	    			transliterations.put(langCode, nameInThatLang);
	    		} catch (NullPointerException e) {
	    			// do nothing.
	    		}
	    	}
		}
		return transliterations;
	}
	
	public static void main (String argv []) throws SAXParseException, SAXException, ParserConfigurationException, IOException {
		NameCrawler nameCrawler = new NameCrawler();
		HashMap<String, String> transliterations = nameCrawler.getTransliterations("Barack Obama");
		
		// write the column names
		System.out.print("en");
		ArrayList<String> langCodes = new ArrayList<String>(transliterations.keySet());
		Collections.sort(langCodes);
		for(String langCode : langCodes) {
			System.out.print("\t" + langCode);
		}
		System.out.println();
		
		for(int year = 2015; year > 0; year--) {
			ArrayList<String> nameList = nameCrawler.getEnglishNamesForYear(year);
			System.err.println(year + "\t" + nameList.size());
			for(String name : nameList) {
				transliterations = nameCrawler.getTransliterations(name);
				// print out the transliterations
				System.out.print(name);
				for(String langCode : langCodes) {
					String transliteration = transliterations.get(langCode);
					if(transliteration != null) {
						System.out.print("\t" + transliteration);
					} else {
						System.out.print("\t");
					}
				}
				System.out.println();
			}
		}
	}//end of main

}
