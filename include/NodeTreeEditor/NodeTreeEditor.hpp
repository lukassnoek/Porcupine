#ifndef NODETREEMODEL_H
#define NODETREEMODEL_H

#include <QStandardItemModel>
#include <QFrame>

class Node;
class NodeTreeItem;
class CodeEditor;
class QDomDocument;
class QDomElement;
class QVBoxLayout;

class NodeTreeEditor : public QFrame
{
    Q_OBJECT
public:
    //
    NodeTreeEditor(
            QWidget* _parent
            );
    //
    void addNode(
            const Node* _node
            );
    //
    void removeNode(
            const Node* _node
            );
    //
    void saveToXml(
            QDomElement& _xmlFile
            ) const;
    //
    void setCodeEditor(
            CodeEditor* _editor
            );
    //
    void generateCode(
            );
    //
    void updateNodeOrder(
            );
    //
    ~NodeTreeEditor(
            );
public slots:
    /// @brief receives signal that _item just swapped places, so the nodes need to be reordered.
    void nodeMoved(
            NodeTreeItem* _item
            );
    /// @when a new link is created, the node list needs to be checkd for correctness and perhaps restructured
    void linkCreated(
            const Node* _from,
            const Node* _to
            );
private:
    //
    QVBoxLayout* m_layout;
    //
    QVector<const Node*> m_nodes;
    //
    QList<NodeTreeItem*> m_nodeList;
    //
    CodeEditor* m_codeEditor;
    //
    NodeTreeItem* getNodeTreeItem(
            const Node* _node
            );
    //
    QVector<NodeTreeItem*> getNodeTreeItems(
            QVector<const Node*> _nodes
            );
    //
    int nodeIndexInList(
            const Node* _node
            );
    //
    QList<int> nodeIndexInList(
            QVector<const Node*> _nodes
            );
};

#endif // NODETREEMODEL_H