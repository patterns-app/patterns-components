# Salesforce case classification with Cohere

1. Configure **Setup > Remote Site Setting** with `https://api.patterns.app`
2. Create the following **Apex trigger**:

```java
trigger CaseClassifier on Case (after insert) {
    if(!Trigger.new.isEmpty()) {
        Patterns.sendToPatterns(Trigger.newMap.keySet());
    }
}
```

> Salesforce does not support webhooks, so we can call this with code

3. Create the following **Apex class**:
```java
public class Patterns
{    
    @future(callout=true)
    public static void sendToPatterns(Set<Id> caseIds) {
        List<Case> cases = [SELECT Id, Subject FROM Case WHERE Id IN: caseIds];

        HttpRequest request = new HttpRequest();
        request.setEndpoint('your-webhook-url');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setBody(JSON.serialize(cases));
        
        Http http = new Http();
        HttpResponse response = http.send(request);
        String responseBody = response.getBody();
        
        System.debug('Response: ' + responseBody);
    }
}
```

After configuring each node with connections and running, any new Case record will be classified and automatically configure a "Type" based on the Case's subject.